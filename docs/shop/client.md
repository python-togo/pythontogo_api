# Shop Client — Guide de test
**Base URL :** `/api/v2/shop`

> Les routes publiques ne nécessitent pas de token.  
> Les routes panier et commandes nécessitent : `Authorization: Bearer <access_token>`

---

## Ordre de test recommandé

```
1. Auth          → créer un compte et se connecter
2. Catalogue     → parcourir les catégories et produits (sans connexion)
3. Panier        → ajouter des articles, modifier, appliquer un coupon
4. Checkout      → passer la commande
5. Mes commandes → vérifier que la commande apparaît
```

---

## 1. Auth — Créer un compte et se connecter

### `POST /api/v2/auth/register`
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "motdepasse",
  "full_name": "John Doe"
}
```

**Réponse 201**
```json
{
  "id": "uuid-user",
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "member",
  "is_active": true,
  "created_at": "2026-04-19T10:00:00Z"
}
```

---

### `POST /api/v2/auth/login`
```json
{
  "email": "john@example.com",
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

> Utiliser `access_token` dans le header `Authorization: Bearer <access_token>` pour les routes protégées.

---

## 2. Catalogue (sans connexion)

### `GET /categories`
Pas de body. Liste toutes les catégories actives.

**Réponse 200**
```json
[
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
]
```

---

### `GET /categories/{category_id}`
Pas de body.

**Réponse 200** — objet catégorie.

---

### `GET /products`
Pas de body. Paramètres query optionnels :

| Paramètre | Type | Description |
|---|---|---|
| `event_id` | UUID | Filtrer par événement |
| `category_id` | UUID | Filtrer par catégorie |

Exemples :
```
GET /api/v2/shop/products
GET /api/v2/shop/products?event_id=uuid-event
GET /api/v2/shop/products?category_id=uuid-category
```

**Réponse 200**
```json
[
  {
    "id": "uuid-product",
    "event_id": "uuid",
    "category_id": "uuid",
    "name": "T-Shirt PyCon TG 2026",
    "slug": "t-shirt-pycon-tg-2026",
    "description": "T-shirt officiel de l'édition 2026",
    "image_url": "https://cdn.example.com/tshirt.png",
    "base_price": "15.00",
    "is_active": true,
    "created_at": "2026-04-19T10:00:00Z",
    "updated_at": "2026-04-19T10:00:00Z"
  }
]
```

---

### `GET /products/{product_id}`
Pas de body. Retourne le produit **avec toutes ses variantes actives**.

**Réponse 200**
```json
{
  "id": "uuid-product",
  "event_id": "uuid",
  "category_id": "uuid",
  "name": "T-Shirt PyCon TG 2026",
  "slug": "t-shirt-pycon-tg-2026",
  "description": "T-shirt officiel de l'édition 2026",
  "image_url": "https://cdn.example.com/tshirt.png",
  "base_price": "15.00",
  "is_active": true,
  "created_at": "2026-04-19T10:00:00Z",
  "updated_at": "2026-04-19T10:00:00Z",
  "variants": [
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
  ]
}
```

> Si `price_override` est null, le prix est `base_price` du produit.  
> Conserver le `variant_id` pour l'ajouter au panier.

---

## 3. Panier — Auth requise

Le panier est stocké en session Redis (TTL 7 jours). Il est vidé automatiquement après un checkout réussi.

### `POST /cart/items`
Ajouter un article au panier.

Header : `Authorization: Bearer <access_token>`

**Body**
```json
{
  "variant_id": "uuid-variant",
  "quantity": 2
}
```
> Si la variante est déjà dans le panier, la quantité est **additionnée**.  
> Retourne `400` si le stock est insuffisant.

**Réponse 201**
```json
{
  "items": [
    {
      "variant_id": "uuid-variant",
      "quantity": 2,
      "sku": "TSHIRT-2026-L-BLUE",
      "name": "T-Shirt PyCon TG 2026 — Taille L — Bleu",
      "unit_price": "15.00",
      "subtotal": "30.00"
    }
  ],
  "coupon_code": null,
  "subtotal": "30.00",
  "discount_amount": "0.00",
  "total": "30.00"
}
```

---

### `GET /cart`
Voir le contenu du panier.

Header : `Authorization: Bearer <access_token>`  
Pas de body.

**Réponse 200** — même structure que ci-dessus.

---

### `PUT /cart/items/{variant_id}`
Modifier la quantité d'un article.

Header : `Authorization: Bearer <access_token>`

**Body**
```json
{
  "quantity": 3
}
```
> Remplace la quantité existante.

**Réponse 200** — panier mis à jour.

---

### `DELETE /cart/items/{variant_id}`
Retirer un article du panier.

Header : `Authorization: Bearer <access_token>`  
Pas de body.

**Réponse 200** — panier mis à jour.

---

### `DELETE /cart`
Vider complètement le panier.

Header : `Authorization: Bearer <access_token>`  
Pas de body.

**Réponse 204** — pas de contenu.

---

## 4. Checkout — Auth requise

### `POST /cart/checkout`
Header : `Authorization: Bearer <access_token>`

**Body**
```json
{
  "event_id": "uuid-event",
  "shipping_address": {
    "full_name": "John Doe",
    "address": "12 rue de la Paix",
    "city": "Lomé",
    "country": "Togo"
  },
  "coupon_code": "PYCON2026"
}
```
> `coupon_code` et `shipping_address` sont optionnels.

**Ce qui se passe automatiquement :**
1. Validation du stock pour chaque article
2. Validation du coupon (actif, non expiré, non épuisé)
3. Calcul du total avec réduction
4. Création de la commande et ses lignes en base de données
5. Décrémentation des stocks
6. Incrémentation du compteur du coupon
7. Vidage du panier Redis

**Réponse 201**
```json
{
  "id": "uuid-order",
  "event_id": "uuid",
  "user_id": "uuid",
  "coupon_id": "uuid-coupon",
  "status": "pending",
  "total_amount": "25.50",
  "discount_amount": "4.50",
  "shipping_address": {
    "full_name": "John Doe",
    "address": "12 rue de la Paix",
    "city": "Lomé",
    "country": "Togo"
  },
  "created_at": "2026-04-19T10:00:00Z",
  "updated_at": "2026-04-19T10:00:00Z"
}
```

> Conserver l'`id` de la commande pour la consulter ensuite.

---

## 5. Mes commandes — Auth requise

### `GET /orders/me`
Header : `Authorization: Bearer <access_token>`  
Pas de body.

**Réponse 200**
```json
[
  {
    "id": "uuid-order",
    "event_id": "uuid",
    "user_id": "uuid",
    "coupon_id": null,
    "status": "pending",
    "total_amount": "30.00",
    "discount_amount": "0.00",
    "shipping_address": {},
    "created_at": "2026-04-19T10:00:00Z",
    "updated_at": "2026-04-19T10:00:00Z"
  }
]
```

---

### `GET /orders/me/{order_id}`
Header : `Authorization: Bearer <access_token>`  
Pas de body.

**Réponse 200** — commande avec ses lignes :
```json
{
  "id": "uuid-order",
  "event_id": "uuid",
  "user_id": "uuid",
  "coupon_id": null,
  "status": "pending",
  "total_amount": "30.00",
  "discount_amount": "0.00",
  "shipping_address": {
    "full_name": "John Doe",
    "address": "12 rue de la Paix",
    "city": "Lomé",
    "country": "Togo"
  },
  "created_at": "2026-04-19T10:00:00Z",
  "updated_at": "2026-04-19T10:00:00Z",
  "items": [
    {
      "id": "uuid",
      "order_id": "uuid-order",
      "product_variant_id": "uuid-variant",
      "quantity": 2,
      "unit_price": "15.00",
      "created_at": "2026-04-19T10:00:00Z"
    }
  ]
}
```

> Un client ne peut voir **que ses propres commandes**.

---

## Codes d'erreur communs

| Code | Signification |
|---|---|
| `400` | Panier vide / stock insuffisant / coupon invalide ou expiré |
| `401` | Token manquant ou expiré |
| `404` | Ressource introuvable |
