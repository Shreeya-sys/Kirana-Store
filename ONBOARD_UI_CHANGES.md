# UI Changes Required for Shop Onboarding and Login

## Backend Changes Completed

### 1. Added `shop_id` to Onboard API Response
- The `ShopOnboardResponse` now includes `shop_id` explicitly
- Response structure:
  ```json
  {
    "shop": { ... },
    "owner": { ... },
    "shop_id": 123,  // <-- New field
    "message": "..."
  }
  ```

### 2. Duplicate Shop Name Validation
- **During Onboarding**: If a shop with the same name already exists, the API returns:
  ```json
  {
    "detail": "A shop with the name 'ShopName' already exists. Please use a different shop name or contact support if you need to access an existing shop."
  }
  ```
  Status: `400 Bad Request`

- **During Login**: If someone tries to login using shop_name instead of shop_code:
  - If multiple shops exist with that name: Error message explaining to use shop_code
  - If only one shop exists: Error message with the correct shop_code

## Frontend UI Changes Required

### 1. Onboarding Screen (`features/shop/onboard_screen.dart`)

**Display shop_id in success message:**
```dart
// After successful onboarding, show:
Text('Shop ID: ${response.shop_id}')
Text('Shop Code: ${response.shop.shop_code}')
Text('API Key: ${response.shop.api_key}')
```

**Handle duplicate shop name error:**
```dart
try {
  final response = await onboardShop(data);
  // Show success
} on ApiException catch (e) {
  if (e.message.contains('already exists')) {
    // Show user-friendly error:
    // "A shop with this name already exists. Please choose a different name."
    // Optionally: "Do you want to login instead?"
  }
}
```

### 2. Login Screen (`features/auth/login_screen.dart`)

**Show clear distinction between shop_code and shop_name:**
- Label: "Shop Code" (not "Shop Name")
- Helper text: "Use your unique shop code, not the shop name"
- Placeholder: "e.g., SHOPNA1234"

**Handle login errors:**
```dart
try {
  final response = await shopLogin(shopCode, password);
  // Navigate to dashboard
} on ApiException catch (e) {
  if (e.message.contains('Multiple shops found')) {
    // Show error: "Multiple shops found with this name. Please use your shop code."
    // Show link: "Forgot your shop code? Contact support"
  } else if (e.message.contains('shop_code is:')) {
    // Extract and show the correct shop_code from error message
    // "Your shop code is: SHOPNA1234"
  }
}
```

### 3. Error Messages to Display

**Duplicate Shop Name (Onboarding):**
```
⚠️ Shop Name Already Exists

A shop with the name "[shop_name]" already exists.

Options:
- Choose a different shop name
- Contact support if you need to access an existing shop
- [Login instead] button
```

**Multiple Shops with Same Name (Login):**
```
⚠️ Multiple Shops Found

Multiple shops exist with this name. Please use your unique shop code to login.

Your shop code is a unique identifier like: SHOPNA1234

[Forgot your shop code?] Contact support
```

**Single Shop Found (Login with name instead of code):**
```
ℹ️ Use Shop Code

Please use your shop_code to login, not the shop name.

Your shop code is: [SHOP_CODE]

[Login with this code] button
```

## API Response Examples

### Successful Onboarding Response
```json
{
  "shop": {
    "id": 1,
    "shop_name": "My Shop",
    "shop_code": "MYSHOP1234",
    "api_key": "kf_...",
    ...
  },
  "owner": { ... },
  "shop_id": 1,
  "message": "Shop onboarded successfully..."
}
```

### Duplicate Shop Name Error
```json
{
  "detail": "A shop with the name 'My Shop' already exists. Please use a different shop name or contact support if you need to access an existing shop."
}
```

### Login Error (Multiple Shops)
```json
{
  "detail": "Multiple shops found with name 'My Shop'. Please use your unique shop_code to login, not the shop name. Contact support if you need help finding your shop_code."
}
```

## Testing Checklist

- [ ] Test onboarding with duplicate shop name → Should show error
- [ ] Test onboarding with unique shop name → Should succeed
- [ ] Test login with shop_code → Should succeed
- [ ] Test login with shop_name (multiple shops exist) → Should show error
- [ ] Test login with shop_name (single shop exists) → Should show shop_code
- [ ] Verify shop_id is displayed in onboarding success screen
- [ ] Verify error messages are user-friendly
