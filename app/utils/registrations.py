from app.database.orm import insert, select, update, select_with_join, select_with_multiple_joins
from app.schemas.models import MessageResponse, RegistrationCreate, RegistrationUpdate, RegistrationSummary
from uuid import uuid4, UUID
from app.utils.date_format import format_date
from app.utils.tickets import update_ticket, get_ticket_by_id
from app.utils.send_email import send_email_for_confirme_your_ticket_purchase, send_email_for_pass, send_email_for_student_proof_of_enrollment,  send_email_to_ticketing_team
from json import dumps
from fastapi import HTTPException
from app.core.settings import logger, settings
from app.utils.vauchers import update_voucher, calculate_discounted_price
from datetime import datetime, timezone


async def get_all_registrations(db, event_id: UUID | None = None):
    try:
        filter_data = {}
        if event_id:
            filter_data["event_id"] = str(event_id)
        registrations = await select_with_join(
            db,
            table="registrations",
            join_table="tickets",
            join_condition="registrations.ticket_id = tickets.id",
            filter=filter_data,
            columns=[
                "registrations.id",
                "registrations.full_name",
                "registrations.email",
                "registrations.ticket_type",
                "registrations.ticket_quantity",
                "registrations.attendance_status",
                "registrations.payment_status",
                "registrations.payment_reference",
                "registrations.created_at",
                "registrations.updated_at",
                "registrations.event_id",
                "tickets.name",
            ],
        )
        return registrations
    except Exception as e:
        logger.error(f"Error retrieving registrations: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving registrations")


def validate_registration_data(registration: RegistrationCreate, reg_existing, ticket):
    """
    Validate the registration data.
    """
    if not registration.full_name:
        raise HTTPException(
            status_code=400, detail="Full name is required")
    if not registration.email:
        raise HTTPException(
            status_code=400, detail="Email is required")
    if not registration.whatsapp_number:
        raise HTTPException(
            status_code=400, detail="WhatsApp number is required")
    if not registration.ticket_id:
        raise HTTPException(
            status_code=400, detail="Ticket ID is required")
    if not registration.quantity or registration.quantity < 1:
        raise HTTPException(
            status_code=400, detail="Quantity must be at least 1")


async def create_registration(db_pool, registration: RegistrationCreate, event_id: UUID, is_student=False, is_free_ticket=False, discount_code: str | None = None, description: str = ""):
    """
    Create a new registration for an event.
    """
    payment_link = registration.payment_link
    payment_reference = registration.payment_reference
    _to = registration.email
    _action_url = payment_link
    _action_text = "Confirm Your Ticket Purchase"
    _first_name = registration.full_name.split()[0]
    last_name = registration.full_name.split()[-1]
    current_time = datetime.now(timezone.utc)
    reg_id = str(uuid4())

    registration_data = {
        "full_name": registration.full_name,
        "email": registration.email,
        "whatsapp_number": registration.whatsapp_number,
        "ticket_type": registration.ticket_type,
        "ticket_id": registration.ticket_id,
        "ticket_price": registration.ticket_price,
        "ticket_quantity": registration.quantity,
        "attendance_status": registration.attendance_status,
        "payment_status": registration.payment_status,
        "dietary_restrictions": registration.dietary_restrictions,
        "payment_reference": registration.payment_reference,
        "payment_link": registration.payment_link,
        "agreed_to_code_of_conduct": registration.agreed_to_code_of_conduct,
        "agreed_to_privacy_policy": registration.agreed_to_privacy_policy,
        "shared_with_sponsors": registration.shared_with_sponsors,
        "voucher_id": registration.voucher_id,
        "voucher_code": registration.voucher_code,
        "description": description
    }

    async with db_pool.connection() as connection:

        reg_existing = await select_with_join(connection, table="registrations", join_table="tickets", join_condition="registrations.ticket_id = tickets.id", filter={"registrations.email": registration.email, "registrations.event_id": event_id}, columns=["registrations.payment_status", "registrations.id", "registrations.full_name", "registrations.email", "registrations.ticket_quantity", "registrations.payment_link", "registrations.ticket_type", "registrations.ticket_price", "registrations.whatsapp_number", "registrations.ticket_id", "tickets.quantity", "tickets.name"])

        if is_free_ticket:
            registration_data["payment_status"] = "completed"
            if discount_code:
                voucher = await select(connection, "vouchers", filter={"code": discount_code})
                if voucher:
                    already_used_by_user_emails = voucher[0].get("already_used_by_user_emails", [
                    ]) if isinstance(voucher[0].get("already_used_by_user_emails"), list) else []
                    number_of_uses = voucher[0].get("number_of_uses_left", 0)
                    number_of_uses += 1  # Increment the number of uses by 1

                    if registration.email.strip() not in already_used_by_user_emails:
                        already_used_by_user_emails.append(
                            registration.email.strip())
                        await update_voucher(connection, voucher[0]["id"], {"number_of_uses_left": voucher[0]["number_of_uses_left"] - 1, "already_used_by_user_emails": already_used_by_user_emails, "number_of_uses": number_of_uses})

            send_email_for_pass(to=registration_data["email"].strip(), first_name=registration_data["full_name"].split()[0], full_name=registration_data["full_name"],
                                ticket_id=payment_reference, pass_type=registration_data["ticket_type"], number_of_slots=registration_data["ticket_quantity"])
            send_email_to_ticketing_team(name=registration_data["full_name"], email=registration_data["email"], ticket_type=registration_data["ticket_type"],
                                         amount=registration_data["ticket_price"], payment_status=registration_data["payment_status"], date=current_time, payment_url=registration_data["payment_link"], voucher_code=discount_code, phone=registration_data.get("whatsapp_number", "N/A"))

        if reg_existing:

            if is_student in ["yes", "Yes", "YES", True, "true", "True", "TRUE"]:
                student_proof = {
                    "id": str(uuid4()),
                    "full_name": registration.full_name,
                    "email": registration.email,
                    "registration_id": reg_existing[0]['id'],
                    "file_url": registration.file_url,
                    "file_type": registration.file_type,
                    "is_reviewed": False,
                    "is_approved": False
                }

                await insert(connection, "student_proofs", student_proof)
                # TODO: check if the student proof is already submitted and send email accordingly

            if reg_existing[0]['payment_status'] == "completed":
                logger.info(
                    f"User {registration.email} has already completed registration for event {event_id}")
                # TODO to be improve
                send_email_for_pass(to=reg_existing[0]['email'].strip(), first_name=reg_existing[0]['full_name'].split()[0], full_name=reg_existing[0]['full_name'],
                                    ticket_id=reg_existing[0]['ticket_id'], pass_type=reg_existing[0]['ticket_type'], number_of_slots=reg_existing[0]['ticket_quantity'])
                return MessageResponse(message="You have already completed registration for this event.")
            else:
                logger.info(
                    f"User {registration.email} has already initiated registration for event {event_id}")
                await update(connection, "registrations", filter={"id": reg_existing[0]['id']}, data=registration_data)

                if not is_free_ticket:
                    await send_email_for_confirme_your_ticket_purchase(to=reg_existing[0]['email'].strip(), action_url=payment_link, action_text=_action_text, first_name=reg_existing[0]['full_name'].split()[
                        0], last_name=reg_existing[0]['full_name'].split()[-1])
                    send_email_to_ticketing_team(name=reg_existing[0]['full_name'], email=reg_existing[0]['email'], ticket_type=reg_existing[0]['ticket_type'],
                                                 amount=reg_existing[0]['ticket_price'], payment_status=reg_existing[0]['payment_status'], date=current_time, payment_url=reg_existing[0]['payment_link'], voucher_code=discount_code, phone=registration_data.get("whatsapp_number", "N/A"))
                    return MessageResponse(message="Please check your email to confirm your ticket purchase.")
                return MessageResponse(message="Registration successful")

        reg_id = str(uuid4())

        registration_data.update({
            "id": reg_id,
            "event_id": event_id
        })

        await insert(connection, "registrations", registration_data)

        if is_student in ["yes", "Yes", "YES", True, "true", "True", "TRUE"]:
            student_proof = {
                "id": str(uuid4()),
                "full_name": registration.full_name,
                "email": registration.email,
                "registration_id": reg_id,
                "file_url": registration.file_url,
                "file_type": registration.file_type,
                "is_reviewed": False,
                "is_approved": False
            }
            await insert(connection, "student_proofs", student_proof)
        if is_free_ticket:
            send_email_for_pass(to=registration_data["email"].strip(), first_name=registration_data["full_name"].split()[0], full_name=registration_data["full_name"],
                                ticket_id=payment_reference, pass_type=registration_data["ticket_type"], number_of_slots=registration_data["ticket_quantity"])
            send_email_to_ticketing_team(name=registration_data["full_name"], email=registration_data["email"], ticket_type=registration_data["ticket_type"],
                                         amount=registration_data["ticket_price"], payment_status=registration_data["payment_status"], date=current_time, payment_url=registration_data["payment_link"], voucher_code=discount_code, phone=registration_data.get("whatsapp_number", "N/A"))
        else:
            await send_email_for_confirme_your_ticket_purchase(to=_to.strip(), action_url=_action_url, action_text=_action_text, first_name=_first_name, last_name=last_name)
            send_email_to_ticketing_team(name=registration_data["full_name"], email=registration_data["email"], ticket_type=registration_data["ticket_type"],
                                         amount=registration_data["ticket_price"], payment_status=registration_data["payment_status"], date=current_time, payment_url=registration_data["payment_link"], voucher_code=discount_code, phone=registration_data.get("whatsapp_number", "N/A"))
    return MessageResponse(message="Registration successful")


async def update_registration(request, registration_update: RegistrationUpdate):
    """
    Update an existing registration.
    """
    payment_reference = registration_update.get("payment_reference", "")
    description = registration_update.get("description", "")
    payment_id = payment_reference.replace("_", "")
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    async with request.app.state.db_pool.connection() as db:

        existing_registration = await select_with_join(db, table="registrations", join_table="tickets", join_condition="registrations.ticket_id = tickets.id", filter={"registrations.payment_reference": payment_reference}, columns=["registrations.full_name", "registrations.ticket_type", "registrations.id", "registrations.email", "registrations.whatsapp_number", "registrations.ticket_quantity", "registrations.ticket_price",  "registrations.payment_link", "registrations.ticket_id", "tickets.quantity", "tickets.name", "registrations.voucher_id", "registrations.voucher_code"])

        if not existing_registration:
            return MessageResponse(message="Registration not found")

        student_proof = await select(db, "student_proofs", filter={"registration_id": existing_registration[0]['id'], "full_name": existing_registration[0]['full_name'], "email": existing_registration[0]['email']}) if existing_registration else None

        ticket_available = existing_registration[0]['quantity'] - \
            existing_registration[0]['ticket_quantity']

        update_data = registration_update
        update_data['ticket_type'] = existing_registration[0]['name']

        await request.app.state.redis_client.set(f"ticket_registration_token:{payment_reference}", payment_reference, ex=3600)
        await update(db, "registrations", filter={"description": description}, data=update_data)
        await update_ticket(db, existing_registration[0]['ticket_id'], {"quantity": ticket_available})

        if existing_registration[0]['voucher_id']:
            voucher = await select(db, "vouchers", filter={"id": existing_registration[0]['voucher_id']})

            if voucher:
                already_used_by_user_emails = voucher[0].get("already_used_by_user_emails", [
                ]) if isinstance(voucher[0].get("already_used_by_user_emails"), list) else []
                number_of_uses = voucher[0].get("number_of_uses_left", 0)
                number_of_uses += 1  # Increment the number of uses by 1

                if existing_registration[0]['email'] not in already_used_by_user_emails:
                    already_used_by_user_emails.append(
                        existing_registration[0]['email'])
                await update_voucher(db=db, voucher_id=voucher[0]["id"], voucher_data={"number_of_uses_left": voucher[0]["number_of_uses_left"] - 1, "already_used_by_user_emails": already_used_by_user_emails, "number_of_uses": number_of_uses})

            try:
                existing_reg = await select_with_multiple_joins(db, table="registrations", joins=[
                    {"join_table": "vouchers",
                        "join_condition": "registrations.voucher_id = vouchers.id"},
                    {"join_table": "events",
                        "join_condition": "registrations.event_id = events.id"}
                ], filter={"registrations.description": description}, columns=["events.title",   "registrations.ticket_type", "registrations.ticket_price", "registrations.voucher_code", "vouchers.discount_percentage", "vouchers.discount_amount", "vouchers.referer_info"])

                if existing_reg:
                    referer_info = existing_reg[0].get("referer_info", {})
                    if referer_info and referer_info.get("referer_email", ""):
                        current_time = request.app.state.current_time.strftime(
                            "%Y-%m-%d %H:%M:%S")
                        from app.utils.send_email import send_email_for_affiliation
                        from app.utils.referal import calculate_commission_amount

                        commission_amount = calculate_commission_amount(
                            existing_reg[0]['ticket_price'], referer_info.get("referer_commission_percentage", 0))
                        send_email_for_affiliation(to=referer_info.get("referer_email", ""), affiliate_name=referer_info.get("referer_full_name", ""), ticket_name=existing_reg[0][
                            'ticket_type'], commission_amount=commission_amount, purchase_date=current_time, referral_id=existing_reg[0]['voucher_code'], event_name=existing_reg[0]['title'])
            except Exception as e:
                logger.error(
                    f"Error sending affiliation email: {str(e)}")
                # Optionally, you can raise an HTTPException here if you want to notify the user about the failure
                # raise HTTPException(status_code=500, detail="Failed to send affiliation email")

        if student_proof or existing_registration[0]['ticket_type'].lower().strip() in ["student", "student pass", "student ticket", "etudiant", "etudiant pass", "etudiant ticket"]:
            submission_date = format_date(student_proof[0]['created_at'])
            document_name = student_proof[0]['file_url'].split("/")[-1]
            document_url = student_proof[0]['file_url']
            send_email_for_student_proof_of_enrollment(to=existing_registration[0]['email'].strip(), first_name=existing_registration[0]['full_name'].split(
            )[0], full_name=existing_registration[0]['full_name'], proof_id=payment_id, submission_date=submission_date, document_name=document_name, document_url=document_url)
            return MessageResponse(message="Registration updated successfully")

        send_email_for_pass(to=existing_registration[0]['email'], first_name=existing_registration[0]['full_name'].split()[0], full_name=existing_registration[0]['full_name'],
                            ticket_id=payment_id, pass_type=existing_registration[0]['name'], number_of_slots=existing_registration[0]['ticket_quantity'])
        send_email_to_ticketing_team(name=existing_registration[0]['full_name'], email=existing_registration[0]['email'], ticket_type=existing_registration[0]['name'],
                                     amount=existing_registration[0]['ticket_price'], payment_status="completed", date=current_time, payment_url=existing_registration[0]['payment_link'], voucher_code=existing_registration[0]['voucher_code'], phone=existing_registration[0].get("whatsapp_number", "N/A"))

    return MessageResponse(message="Registration updated successfully")


async def approve_student_registration(db, registration_id: str):
    """
    Approve a student registration.
    """
    try:
        # registration = await select(db, "registrations", filter={"id": registration_id})
        student_reg = await select_with_join(db, table="registrations", join_table="student_proofs", join_condition="registrations.id = student_proofs.registration_id", filter={"registrations.id": registration_id}, columns=[
            "registrations.full_name", "registrations.email", "registrations.payment_reference", "registrations.ticket_type", "registrations.ticket_quantity", "student_proofs.file_url", "student_proofs.file_type", "student_proofs.is_reviewed", "student_proofs.is_approved"])
        if not student_reg:
            return MessageResponse(message="Registration not found")

        send_email_for_pass(to=student_reg[0]['email'].strip(), first_name=student_reg[0]['full_name'].split()[0], full_name=student_reg[0]['full_name'],
                            ticket_id=student_reg[0]['payment_reference'], pass_type=student_reg[0]['ticket_type'], number_of_slots=student_reg[0]['ticket_quantity'])

        await update(db, "student_proofs", filter={"registration_id": registration_id}, data={
            "is_reviewed": True, "is_approved": True})
        return MessageResponse(message="Student registration approved successfully")
    except Exception as e:
        logger.error(f"Error approving student registration: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import asyncio
    from psycopg import AsyncConnection

    payment_reference = "test_q1fbjbe7o8"

    async def main():
        db = await AsyncConnection.connect(settings.db_url)

        registration = await select_with_multiple_joins(
            db,
            table="registrations",
            joins=[
                {"join_table": "vouchers",
                 "join_condition": "registrations.voucher_id = vouchers.id"},
                {"join_table": "events",
                 "join_condition": "registrations.event_id = events.id"}
            ],
            filter={
                "registrations.payment_reference": payment_reference
            },
            columns=[
                "events.title",
                "registrations.ticket_type",
                "registrations.ticket_price",
                "vouchers.code",
                "vouchers.discount_percentage",
                "vouchers.discount_amount",
                "vouchers.referer_info"
            ]
        )

        reg = await select_with_join(
            db,
            table="registrations",
            join_table="vouchers",
            join_condition="registrations.voucher_id = vouchers.id",
            filter={
                "registrations.payment_reference": payment_reference
            }
        )

        print(f"Registration with voucher: {registration}")
        # print(f"Registration: {reg}")

        await db.close()

    asyncio.run(main())
