# Shop Admin — Guide de test
**Base URL :** `/api/v2/admin/shop`  
**Auth requise sur tous les endpoints :** `Authorization: Bearer <access_token>` (role `admin` ou `staff`)

---

## Ordre de test recommandé

```
1. Auth          → obtenir un token admin
2. Catégories    → créer les catégories (nécessaires pour les produits)
3. Produits      → créer les produits (nécessite event_id + category_id)
4. Variantes     → ajouter les variantes à chaque produit
5. Coupons       → créer les codes promo
6. Commandes     → consulter et gérer les commandes passées par les clients
7. Paiements     → consulter l'historique des paiements
8. Clients       → gérer les comptes clients
9. Dashboard     → vérifier les statistiques globales
```

---

## 1. Auth — Obtenir un token admin

> Les endpoints admin nécessitent un compte avec `role = admin` ou `staff`.  
> Créer le compte via `POST /api/v2/auth/register` puis se connecter.

### `POST /api/v2/auth/login`
```json
{
  "email": "admin@pytogo.org",
  "password": "motdepasse"
}
```

**Réponse 200**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

> Utiliser `access_token` dans le header `Authorization: Bearer <access_token>` pour tous les appels suivants.

---

## 2. Catégories

### `POST /categories`
À faire en premier — les produits ont besoin d'un `category_id`.

**Body**
```json
{
  "name": "T-Shirts",
  "slug": "t-shirts",
  "description": "Vêtements officiels PyCon TG",
  "parent_id": null,
  "is_active": true
}
```
> `description` et `parent_id` sont optionnels.

**Réponse 201**
```json
{
  "id": "uuid-category",
  "name": "T-Shirts",
  "slug": "t-shirts",
  "description": "Vêtements officiels PyCon TG",
  "parent_id": null,
  "is_active": true,
  "created_at": "2026-04-19T10:00:00Z",
  "updated_at": "2026-04-19T10:00:00Z"
}
```

> Conserver l'`id` retourné — il sera utilisé comme `category_id` dans les produits.

---

### `GET /categories`
Pas de body. Vérifier que la catégorie créée apparaît.

**Réponse 200** — liste de catégories.

---

### `GET /categories/{category_id}`
Pas de body.

**Réponse 200** — objet catégorie.

---

### `PUT /categories/{category_id}`
**Body** — tous les champs sont optionnels :
```json
{
  "name": "T-Shirts PyCon",
  "slug": "t-shirts-pycon",
  "description": "Nouvelle description",
  "parent_id": null,
  "is_active": true
}
```

**Réponse 200** — catégorie mise à jour.

---

### `PATCH /categories/{category_id}/toggle`
Pas de body. Inverse `is_active` de la catégorie.

> Une catégorie désactivée n'apparaît plus dans le catalogue client.  
> Les produits liés restent dans leur état — c'est `is_active` du produit qui contrôle leur visibilité.

**Réponse 200** — objet catégorie avec `is_active` mis à jour.

---

### `DELETE /categories/{category_id}`
Pas de body.

**Réponse 204** — pas de contenu.

---

## 3. Produits

### `POST /products`
Nécessite un `event_id` existant et un `category_id` créé à l'étape 2.

**Body**
```json
{
  "event_id": "uuid-event",
  "category_id": "uuid-category",
  "name": "T-Shirt PyCon TG 2026",
  "slug": "t-shirt-pycon-tg-2026",
  "description": "T-shirt officiel de l'édition 2026",
  "image_url": "https://cdn.example.com/tshirt.png",
  "base_price": "15.00",
  "is_active": true
}
```
> `category_id`, `description`, `image_url` sont optionnels.

**Réponse 201**
```json
{
  "id": "uuid-product",
  "event_id": "uuid-event",
  "category_id": "uuid-category",
  "name": "T-Shirt PyCon TG 2026",
  "slug": "t-shirt-pycon-tg-2026",
  "description": "T-shirt officiel de l'édition 2026",
  "image_url": "https://cdn.example.com/tshirt.png",
  "base_price": "15.00",
  "is_active": true,
  "created_at": "2026-04-19T10:00:00Z",
  "updated_at": "2026-04-19T10:00:00Z"
}
```

> Conserver l'`id` retourné — il sera utilisé pour ajouter des variantes.

---

### `GET /products`
Pas de body. Vérifier que le produit créé apparaît.

**Réponse 200** — liste de produits.

---

### `GET /products/{product_id}`
Pas de body.

**Réponse 200** — objet produit.

---

### `PUT /products/{product_id}`
**Body** — tous les champs sont optionnels :
```json
{
  "name": "T-Shirt PyCon TG 2026 — Edition limitée",
  "base_price": "20.00",
  "is_active": true
}
```

**Réponse 200** — produit mis à jour.

---

### `PATCH /products/{product_id}/toggle`
Pas de body. Inverse `is_active` du produit.

> Si le produit est **désactivé**, il disparaît du catalogue client et **toutes ses variantes** deviennent invisibles même si elles sont actives individuellement.

**Réponse 200** — produit avec `is_active` mis à jour.

---

### `DELETE /products/{product_id}`
Pas de body.

**Réponse 204** — pas de contenu.

---

## 4. Variantes

### `POST /products/{product_id}/variants`
Ajouter au moins une variante pour que le produit soit achetable.

**Body**
```json
{
  "name": "Taille L — Bleu",
  "sku": "TSHIRT-2026-L-BLUE",
  "price_override": null,
  "stock_quantity": 50,
  "attributes": { "size": "L", "color": "blue" },
  "is_active": true
}
```
> `price_override` optionnel — si null, le `base_price` du produit est utilisé.  
> `attributes` : objet JSON libre pour décrire la variante.

**Réponse 201**
```json
{
  "id": "uuid-variant",
  "product_id": "uuid-product",
  "name": "Taille L — Bleu",
  "sku": "TSHIRT-2026-L-BLUE",
  "price_override": null,
  "stock_quantity": 50,
  "attributes": { "size": "L", "color": "blue" },
  "is_active": true,
  "created_at": "2026-04-19T10:00:00Z",
  "updated_at": "2026-04-19T10:00:00Z"
}
```

> Conserver l'`id` retourné — il sera utilisé par les clients pour ajouter au panier.

---

### `GET /products/{product_id}/variants`
Pas de body.

**Réponse 200** — liste des variantes du produit.

---

### `PUT /products/{product_id}/variants/{variant_id}`
**Body** — tous les champs sont optionnels :
```json
{
  "stock_quantity": 30,
  "price_override": "18.00"
}
```

**Réponse 200** — variante mise à jour.

---

### `PATCH /products/{product_id}/variants/{variant_id}/toggle`
Pas de body. Inverse `is_active` de la variante.

> Une variante désactivée n'apparaît plus dans le catalogue client et ne peut pas être ajoutée au panier.  
> Si elle est dans un panier existant, elle sera ignorée lors du checkout.

**Réponse 200**
```json
{
  "id": "uuid-variant",
  "product_id": "uuid-product",
  "name": "Taille L — Bleu",
  "sku": "TSHIRT-2026-L-BLUE",
  "price_override": null,
  "stock_quantity": 50,
  "attributes": { "size": "L", "color": "blue" },
  "is_active": false,
  "created_at": "2026-04-19T10:00:00Z",
  "updated_at": "2026-04-19T10:00:00Z"
}
```

---

### `DELETE /products/{product_id}/variants/{variant_id}`
Pas de body.

**Réponse 204** — pas de contenu.

---

## 5. Coupons

### `POST /coupons`
**Body**
```json
{
  "event_id": "uuid-event",
  "code": "PYCON2026",
  "type": "percentage",
  "value": "15.00",
  "max_uses": 100,
  "expires_at": "2026-12-31T23:59:59Z",
  "is_active": true
}
```
> `event_id`, `max_uses`, `expires_at` sont optionnels.  
> `type` : `percentage` (valeur en %) ou `fixed_amount` (valeur en monnaie).

**Réponse 201**
```json
{
  "id": "uuid-coupon",
  "event_id": "uuid-event",
  "code": "PYCON2026",
  "type": "percentage",
  "value": "15.00",
  "max_uses": 100,
  "uses_count": 0,
  "expires_at": "2026-12-31T23:59:59Z",
  "is_active": true,
  "created_at": "2026-04-19T10:00:00Z",
  "updated_at": "2026-04-19T10:00:00Z"
}
```

---

### `GET /coupons`
Pas de body.

**Réponse 200** — liste des coupons.

---

### `PUT /coupons/{coupon_id}`
**Body** — tous les champs sont optionnels :
```json
{
  "max_uses": 200,
  "is_active": false
}
```

**Réponse 200** — coupon mis à jour.

---

### `DELETE /coupons/{coupon_id}`
Pas de body.

**Réponse 204** — pas de contenu.

---

## 6. Commandes

> Les commandes sont créées par les clients via `POST /api/v2/shop/cart/checkout`.  
> L'admin peut les consulter et mettre à jour leur statut.

### `GET /orders`
Pas de body. Paramètres query disponibles :

| Paramètre | Type | Description |
|---|---|---|
| `event_id` | UUID | Filtrer par événement |
| `status` | string | Filtrer par statut |
| `user_id` | UUID | Filtrer par client |
| `limit` | int | Nombre max de résultats (défaut `50`, max `500`) |
| `offset` | int | Pagination (défaut `0`) |

Exemples :
```
GET /api/v2/admin/shop/orders?status=pending
GET /api/v2/admin/shop/orders?event_id=uuid&status=paid&limit=20
GET /api/v2/admin/shop/orders?user_id=uuid
```

> Statuts possibles : `pending` | `paid` | `shipped` | `delivered` | `cancelled`

**Réponse 200** — triée par date décroissante :
```json
[
  {
    "id": "uuid",
    "event_id": "uuid",
    "user_id": "uuid",
    "coupon_id": null,
    "status": "pending",
    "total_amount": "35.00",
    "discount_amount": "0.00",
    "shipping_address": {
      "full_name": "Jean Dupont",
      "address": "12 rue de la Paix",
      "city": "Lomé",
      "country": "Togo"
    },
    "created_at": "2026-04-19T10:00:00Z",
    "updated_at": "2026-04-19T10:00:00Z"
  }
]
```

---

### `GET /orders/{order_id}`
Pas de body.

**Réponse 200** — commande avec ses lignes :
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "user_id": "uuid",
  "coupon_id": null,
  "status": "paid",
  "total_amount": "35.00",
  "discount_amount": "5.00",
  "shipping_address": {
    "full_name": "Jean Dupont",
    "address": "12 rue de la Paix",
    "city": "Lomé",
    "country": "Togo"
  },
  "created_at": "2026-04-19T10:00:00Z",
  "updated_at": "2026-04-19T10:00:00Z",
  "items": [
    {
      "id": "uuid",
      "order_id": "uuid",
      "product_variant_id": "uuid",
      "quantity": 2,
      "unit_price": "15.00",
      "created_at": "2026-04-19T10:00:00Z"
    }
  ]
}
```

---

### `PATCH /orders/{order_id}/status`
**Body**
```json
{
  "status": "shipped"
}
```
> Progression logique : `pending` → `paid` → `shipped` → `delivered`  
> Annulation possible à tout moment : `cancelled`

**Réponse 200** — commande mise à jour.

---

## 7. Paiements

> Les paiements sont créés automatiquement lors du checkout.  
> L'admin peut uniquement les consulter.

### `GET /payments`
Pas de body.

**Réponse 200**
```json
[
  {
    "id": "uuid",
    "order_id": "uuid",
    "amount": "35.00",
    "status": "succeeded",
    "method": "mobile_money",
    "reference": "TXN-ABC123",
    "created_at": "2026-04-19T10:00:00Z",
    "updated_at": "2026-04-19T10:00:00Z"
  }
]
```
> Statuts possibles : `pending` | `succeeded` | `failed` | `refunded`

---

### `GET /payments/{payment_id}`
Pas de body.

**Réponse 200** — objet paiement.

---

## 8. Clients

### `GET /customers`
Pas de body.

**Réponse 200**
```json
[
  {
    "id": "uuid",
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "member",
    "is_active": true,
    "created_at": "2026-04-19T10:00:00Z"
  }
]
```

---

### `GET /customers/{customer_id}`
Pas de body.

**Réponse 200** — objet client.

---

### `GET /customers/{customer_id}/orders`
Pas de body.

**Réponse 200** — liste des commandes du client.

---

### `PATCH /customers/{customer_id}/toggle`
Pas de body. Inverse `is_active` (bloquer / débloquer).

**Réponse 200** — client mis à jour.

---

## 9. Dashboard

> À consulter en dernier pour vérifier que toutes les données remontent correctement.

### `GET /dashboard`
Pas de body.

**Réponse 200**
```json
{
  "total_users": 120,
  "total_orders": 45,
  "total_revenue": "1350.00",
  "recent_orders": [
    {
      "id": "uuid",
      "event_id": "uuid",
      "user_id": "uuid",
      "coupon_id": null,
      "status": "paid",
      "total_amount": "35.00",
      "discount_amount": "0.00",
      "shipping_address": {},
      "created_at": "2026-04-19T10:00:00Z",
      "updated_at": "2026-04-19T10:00:00Z"
    }
  ]
}
```

---

## Codes d'erreur communs

| Code | Signification |
|---|---|
| `401` | Token manquant ou expiré |
| `403` | Role insuffisant (`admin` ou `staff` requis) |
| `404` | Ressource introuvable |
| `409` | Conflit — slug, code ou SKU déjà utilisé |
