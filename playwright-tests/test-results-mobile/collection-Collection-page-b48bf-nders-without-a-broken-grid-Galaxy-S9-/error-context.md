# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: collection.spec.ts >> Collection page — subcategories (CL-01..CL-04) >> CL-01/CL-02 subcategory section renders without a broken grid
- Location: tests\collection.spec.ts:5:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: expected at least one collection link on /collections

expect(locator).toBeVisible() failed

Locator:  locator('a[href*="/collections/"]').first()
Expected: visible
Received: hidden
Timeout:  5000ms

Call log:
  - expected at least one collection link on /collections with timeout 5000ms
  - waiting for locator('a[href*="/collections/"]').first()
    6 × locator resolved to <a class="button" href="/collections/all">↵                Continue shopping↵              </a>
      - unexpected value "hidden"

```

```yaml
- banner:
  - group:
    - button "Menu"
  - heading "ZeroGap Supply Co" [level=1]:
    - link "ZeroGap Supply Co":
      - /url: /
      - img "ZeroGap Supply Co"
  - img
  - link:
    - /url: /pages/wishlist
    - img
  - button:
    - img
- main:
  - heading [level=1]
  - text: SHOP BY CATEGORY
  - heading "FIND YOUR CATEGORY" [level=2]
  - paragraph: From strong-hold pomades to post-shave care — browse the full ZeroGap range by category and find exactly what your routine needs.
  - text: 13 CATEGORIES 38 PRODUCTS 100% BARBER-GRADE
  - list:
    - listitem:
      - link "Barber Essentials":
        - /url: /collections/barber-essentials
        - img "Barber Essentials"
      - heading "Barber Essentials" [level=3]:
        - link "Barber Essentials":
          - /url: /collections/barber-essentials
      - paragraph: 11 Items
    - listitem:
      - link "BarberCon":
        - /url: /collections/barbercon
        - img "BarberCon"
      - heading "BarberCon" [level=3]:
        - link "BarberCon":
          - /url: /collections/barbercon
      - paragraph: 1 Item
      - paragraph: BarberCON produces a core range of essential salon accessories, sanitation equipment, and...
    - listitem:
      - heading "Bundles" [level=3]:
        - link "Bundles":
          - /url: /collections/bundles
      - paragraph: 0 Items
    - listitem:
      - heading "Bundles & Kits" [level=3]:
        - link "Bundles & Kits":
          - /url: /collections/bundles-kits
      - paragraph: 0 Items
    - listitem:
      - heading "Clippers, Trimmers & Shavers" [level=3]:
        - link "Clippers, Trimmers & Shavers":
          - /url: /collections/clippers-trimmers-shavers
      - paragraph: 0 Items
    - listitem:
      - link "Hair 2 Beauty Imports":
        - /url: /collections/hair-2-beauty-imports
        - img "Hair 2 Beauty Imports"
      - heading "Hair 2 Beauty Imports" [level=3]:
        - link "Hair 2 Beauty Imports":
          - /url: /collections/hair-2-beauty-imports
      - paragraph: 0 Items
      - paragraph: Hair 2 Beauty Imports serves as a trusted wholesale distributor for beauty...
    - listitem:
      - heading "Hair Products" [level=3]:
        - link "Hair Products":
          - /url: /collections/hair-products
      - paragraph: 0 Items
    - listitem:
      - link "Home page":
        - /url: /collections/frontpage
        - img "Home page"
      - heading "Home page" [level=3]:
        - link "Home page":
          - /url: /collections/frontpage
      - paragraph: 1 Item
  - link "Loading More":
    - /url: /collections?page=2
  - heading "BUNDLE" [level=6]
  - heading "CAN'T DECIDE? BUILD YOUR KIT" [level=2]
  - text: Tell us your routine and save up to 15% when you bundle pomade, beard and shave essentials together.
  - link "Shop Now" [disabled]
  - link "View Bundles" [disabled]
  - paragraph: NEWSLETTER
  - heading "JOIN THE ZEROGAP LIST" [level=2]
  - paragraph: Get grooming tips, product drops, and exclusive offers.
  - textbox "Your email address"
  - button "Subscribe"
- contentinfo:
  - link:
    - /url: /
  - paragraph: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
  - textbox "Your email address"
  - button "Subscribe"
  - heading "Useful links" [level=2]
  - img
  - heading "Help & Support" [level=2]
  - img
  - heading "Resources" [level=2]
  - img
  - list:
    - listitem:
      - link "TW":
        - /url: "#"
        - img
        - text: TW
    - listitem:
      - link "FB":
        - /url: "#"
        - img
        - text: FB
    - listitem:
      - link "IN":
        - /url: "#"
    - listitem:
      - link "Snapchat":
        - /url: "#"
    - listitem:
      - link "Vimeo":
        - /url: "#"
  - text: Payment methods
  - list:
    - listitem:
      - img "American Express"
    - listitem:
      - img "Apple Pay"
    - listitem:
      - img "Google Pay"
    - listitem:
      - img "Mastercard"
    - listitem:
      - img "PayPal"
    - listitem:
      - img "Union Pay"
    - listitem:
      - img "Visa"
  - paragraph: © 2026 ZeroGap Supply Co.
- link "To top":
  - /url: "#collections"
  - img
  - text: To top
- link "Home":
  - /url: /
  - img
  - text: Home
- link "Shop":
  - /url: /collections
  - img
  - text: Shop
- link "Wishlist":
  - /url: /pages/wishlist
  - img
  - text: Wishlist
- link "Log in":
  - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgwOTg1LCJuYmYiOjE3OTI1NzYxODV9.LkIh7kmic5FJsyB_u12DFt62q9t_jkI19EkH9BrUDFw
  - img
  - text: Log in
```

```
Tearing down "context" exceeded the test timeout of 30000ms.
```