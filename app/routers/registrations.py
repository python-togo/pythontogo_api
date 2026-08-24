from app.utils.vauchers import calculate_discounted_price
from app.database.connection import get_db_connection
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from app.core.settings import logger, settings
from app.schemas.models import (
    MessageResponse,
    RegistrationCreate,
    RegistrationSummary,
    RegistrationUpdate,
    StudentProof,
    AttendeeID,
    TicketSubmissionPayload
)
from uuid import uuid4, UUID
import httpx
from app.utils.tickets import get_ticket_by_id
from app.database.orm import select, select_with_join
from app.routers.helper import submit_ticket
from app.utils.registrations import (
    create_registration,
    get_all_registrations,
)
from app.payments.paydunya_service import create_invoice
from app.core.auth import get_current_superuser
from app.database.orm import select as db_select


api_router = APIRouter(tags=["registrations"])
base_url = settings.base_url.rstrip("/")

base_url = f"{base_url}/{settings.root_path.strip('/')}" if settings.root_path else base_url


def event_ticket_reg_checker(request, event_data, registration: RegistrationCreate) -> bool:
    """
    Validate event ticket data.
    """
    auth = request.headers.get("Authorization")
    if not event_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="event or ticket does not exist")
    if event_data[0]["quantity"] < 1 or event_data[0]["quantity"] < registration.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough slots available for the selected ticket. Available quantity: {event_data[0]['quantity']}")
    if event_data[0]["ticket_sales_open_at"] and event_data[0]["ticket_sales_open_at"] > request.app.state.current_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket sales have not opened yet")
    if event_data[0]["ticket_sales_close_at"] and event_data[0]["ticket_sales_close_at"] < request.app.state.current_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket sales have closed")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@api_router.post("/register/{event_code}", status_code=status.HTTP_201_CREATED)
async def register_for_event(request: Request,  payload: TicketSubmissionPayload, event_code: str, background_tasks: BackgroundTasks, db=Depends(get_db_connection), discount_code: str | None = None):
    """
    Register a user for an event.
    """
    try:
        registration, is_student = submit_ticket(payload)

        registration = RegistrationCreate(**registration)
        event_existing = await select_with_join(db, table="events", join_table="tickets", join_condition="events.id = tickets.event_id", filter={"code": event_code.upper(), "tickets.id": registration.ticket_id}, columns=["events.early_bird_sales_close_at", "events.ticket_sales_close_at", "events.ticket_sales_open_at",  "tickets.event_id", "tickets.id", "tickets.early_bird_price", "tickets.name", "tickets.price", "tickets.quantity"])
        temp_ticket_price = int(
            event_existing[0]["price"]) if event_existing else 0

        is_voucher_valid = False
        event_ticket_reg_checker(request, event_existing, registration)

        if event_existing[0]["early_bird_sales_close_at"] and event_existing[0]["early_bird_sales_close_at"] >= request.app.state.current_time:
            temp_ticket_price = int(event_existing[0]["early_bird_price"])

        if discount_code:
            discount_code = discount_code.strip().replace(" ", "-").upper()
            from app.utils.vauchers import validate_voucher
            voucher = await validate_voucher(request, discount_code, event_existing[0]['id'], event_existing[0]['event_id'], registration.email)
            if not voucher:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or inapplicable voucher code")
            # Apply the discount to the ticket price
            is_voucher_valid = True
            registration.voucher_id = voucher['id']
            registration.voucher_code = voucher['code']
            registration.ticket_price = calculate_discounted_price(
                temp_ticket_price, voucher['discount_percentage'], voucher['discount_amount'])
        else:
            registration.ticket_price = temp_ticket_price

        amount = int(registration.ticket_price * registration.quantity)
        reference = str(uuid4()).split('-')[-1].upper()
        description = f"Registration for {event_code.upper()} - {registration.full_name} #{reference}"

        if amount < 200 and is_voucher_valid:
            await request.app.state.redis_client.set(f"ticket_registration_token:{reference}", reference, ex=3600)
            registration.payment_reference = reference
            registration.payment_link = f"{settings.success_page_url}?token={reference}"
            background_tasks.add_task(create_registration, request.app.state.db_pool, registration,
                                      event_existing[0]["event_id"], is_student, is_free_ticket=True, discount_code=discount_code, description=description)
            return {"message": "Registration successful. You have registered for a free ticket.", "is_free_ticket": True, "payment_url": registration.payment_link}

        success_page_url = settings.success_page_url
        cancel_page_url = settings.cancel_page_url

        payment_data = {
            "amount": int(amount),
            "callback_url": settings.webhook_url,
            "description": description,
            "unit_price": int(registration.ticket_price),
            "quantity": int(registration.quantity),
            "name": registration.ticket_type,
            "success_page_url": success_page_url,
            "cancel_page_url": cancel_page_url
        }

        # TODO : Checker for existing registration with same email and event code, if exists, return a message to user to check their email for confirmation link instead of creating a new registration

        result = create_invoice(payment_data)
        payment_reference = result.get("payment_url").split(
            "/")[-1]
        result['is_free_ticket'] = False
        result['message'] = "Registration successful. Please proceed to payment."
        registration.payment_reference = payment_reference
        registration.payment_link = result.get("payment_url")

        background_tasks.add_task(
            create_registration, request.app.state.db_pool, registration, event_existing[0]["event_id"], is_student, is_free_ticket=False, discount_code=discount_code, description=description)

        return result
    except Exception as e:
        logger.error(f"Error creating registration: {str(e)}")
        import traceback
        traceback.print_exc()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.post("/registrations/student/approve")
async def _approve_student_registration(registration_id: AttendeeID, db=Depends(get_db_connection)):
    try:
        from app.utils.registrations import approve_student_registration
        result = await approve_student_registration(db, registration_id.attendee_id)
        return result
    except Exception as e:
        logger.error(f"Error approving student registration: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/registrations", dependencies=[Depends(get_current_superuser)])
async def _list_registrations(request: Request, event_id: UUID | None = None, db=Depends(get_db_connection)):
    try:
        registrations = await get_all_registrations(db, event_id=event_id)
        if not registrations:
            return []
        return registrations
    except Exception as e:
        logger.error(f"Error listing registrations: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Error listing registrations")
