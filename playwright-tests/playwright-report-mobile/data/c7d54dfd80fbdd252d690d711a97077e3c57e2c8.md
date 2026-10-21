# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — update items (UC-01..UC-05) >> UC-01 updating quantity to 0 removes the item or is blocked, consistently
- Location: tests\cart.spec.ts:24:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.goto: Test timeout of 30000ms exceeded.
Call log:
  - navigating to "https://bcppqf-4m.myshopify.com/collections/all", waiting until "load"

```

# Page snapshot

```yaml
- generic [active] [ref=f4e1]:
  - banner [ref=f4e5]:
    - generic [ref=f4e8]:
      - group [ref=f4e10]:
        - button "Menu" [ref=f4e11] [cursor=pointer]
      - heading [level=1] [ref=f4e14]:
        - link [ref=f4e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f4e16]
      - generic [ref=f4e17]:
        - generic [ref=f4e18] [cursor=pointer]
        - link [ref=f4e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f4e25] [cursor=pointer]
  - main [ref=f4e32]:
    - navigation "breadcrumbs collection" [ref=f4e37]:
      - link "Home" [ref=f4e38]:
        - /url: /
      - link "All collections" [ref=f4e42]:
        - /url: /collections
      - generic [ref=f4e46]: Products
    - generic [ref=f4e50]:
      - img "Products" [ref=f4e52]
      - generic [ref=f4e54]:
        - heading "Products" [level=2] [ref=f4e55]
        - generic [ref=f4e56]: 52 PRODUCTS
    - generic [ref=f4e60]:
      - complementary "Filter:" [ref=f4e61]:
        - generic [ref=f4e62]:
          - group [ref=f4e64]:
            - generic "Filter and sort" [ref=f4e65] [cursor=pointer]
            - group:
              - button "Price" [ref=f4e69] [cursor=pointer]
            - group:
              - button "Product type" [ref=f4e73] [cursor=pointer]
            - group:
              - button "Availability" [ref=f4e77] [cursor=pointer]
            - group:
              - button "Brand" [ref=f4e81] [cursor=pointer]
            - option "Featured"
            - option "Most relevant"
            - option "Best selling"
            - option "Alphabetically, A-Z" [selected]
            - option "Alphabetically, Z-A"
            - option "Price, low to high"
            - option "Price, high to low"
            - option "Date, old to new"
            - option "Date, new to old"
          - status [ref=f4e85]:
            - heading "52 products" [level=2] [ref=f4e86]
      - generic [ref=f4e88]:
        - list [ref=f4e89]:
          - listitem [ref=f4e90]:
            - generic [ref=f4e92]:
              - generic [ref=f4e93]:
                - link [ref=f4e95]:
                  - /url: /products/andis-clipper-oil-118ml
                  - img "Andis Clipper Oil 118ml" [ref=f4e97]
                - generic:
                  - list:
                    - listitem [ref=f4e98]:
                      - generic "Add to wishlist" [ref=f4e100] [cursor=pointer]
              - generic [ref=f4e102]:
                - generic [ref=f4e103]: "Vendor:"
                - generic [ref=f4e104]: Andis
                - heading [level=6] [ref=f4e105]:
                  - link "Andis Clipper Oil 118ml" [ref=f4e106]:
                    - /url: /collections/all/products/andis-clipper-oil-118ml
                - generic [ref=f4e109]:
                  - generic [ref=f4e110]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e111]:
                  - button "Sold out Andis Clipper Oil 118ml" [ref=f4e114] [cursor=pointer]:
                    - generic [ref=f4e115]: QUICK ADD
                    - generic [ref=f4e116]: ›
                  - generic [ref=f4e117]: IN STOCK
          - listitem [ref=f4e119]:
            - generic [ref=f4e121]:
              - generic [ref=f4e122]:
                - link [ref=f4e124]:
                  - /url: /products/astra-blades-green-platinum
                  - img "Astra Green Platinum blade packaging" [ref=f4e126]
                - generic:
                  - list:
                    - listitem [ref=f4e127]:
                      - generic "Add to wishlist" [ref=f4e129] [cursor=pointer]
              - generic [ref=f4e131]:
                - generic [ref=f4e132]: "Vendor:"
                - generic [ref=f4e133]: Astra
                - heading [level=6] [ref=f4e134]:
                  - link "Astra Blades Green Platinum" [ref=f4e135]:
                    - /url: /collections/all/products/astra-blades-green-platinum
                - generic [ref=f4e138]:
                  - generic [ref=f4e139]: Regular price
                  - text: $14.50 AUD
                - generic [ref=f4e140]:
                  - button "Sold out Astra Blades Green Platinum" [ref=f4e143] [cursor=pointer]:
                    - generic [ref=f4e144]: QUICK ADD
                    - generic [ref=f4e145]: ›
                  - generic [ref=f4e146]: IN STOCK
          - listitem [ref=f4e148]:
            - generic [ref=f4e150]:
              - generic [ref=f4e151]:
                - link [ref=f4e153]:
                  - /url: /products/barbercon-acrylic-sterilizing-jar-1094ml
                  - generic [ref=f4e154]:
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e155]
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e156]
                - generic:
                  - list:
                    - listitem [ref=f4e157]:
                      - generic "Add to wishlist" [ref=f4e159] [cursor=pointer]
              - generic [ref=f4e161]:
                - generic [ref=f4e162]: "Vendor:"
                - generic [ref=f4e163]: BarberCon
                - heading [level=6] [ref=f4e164]:
                  - link "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e165]:
                    - /url: /collections/all/products/barbercon-acrylic-sterilizing-jar-1094ml
                - generic [ref=f4e168]:
                  - generic [ref=f4e169]: Regular price
                  - text: $27.23 AUD
                - generic [ref=f4e170]:
                  - button "Sold out BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e173] [cursor=pointer]:
                    - generic [ref=f4e174]: QUICK ADD
                    - generic [ref=f4e175]: ›
                  - generic [ref=f4e176]: IN STOCK
          - listitem [ref=f4e178]:
            - generic [ref=f4e180]:
              - generic [ref=f4e181]:
                - link [ref=f4e183]:
                  - /url: /products/barbercon-neck-strips-white
                  - img "BarberCon Neck Strips - White" [ref=f4e185]
                - generic:
                  - list:
                    - listitem [ref=f4e186]:
                      - generic "Add to wishlist" [ref=f4e188] [cursor=pointer]
              - generic [ref=f4e190]:
                - generic [ref=f4e191]: "Vendor:"
                - generic [ref=f4e192]: BarberCon
                - heading [level=6] [ref=f4e193]:
                  - link "BarberCon Neck Strips - White" [ref=f4e194]:
                    - /url: /collections/all/products/barbercon-neck-strips-white
                - generic [ref=f4e197]:
                  - generic [ref=f4e198]: Regular price
                  - text: $6.32 AUD
                - generic [ref=f4e199]:
                  - button "Sold out BarberCon Neck Strips - White" [ref=f4e202] [cursor=pointer]:
                    - generic [ref=f4e203]: QUICK ADD
                    - generic [ref=f4e204]: ›
                  - generic [ref=f4e205]: IN STOCK
          - listitem [ref=f4e207]:
            - generic [ref=f4e209]:
              - generic [ref=f4e210]:
                - link [ref=f4e212]:
                  - /url: /products/barbercon-wax-pot-black
                  - img "BarberCon Wax Pot Black" [ref=f4e214]
                - generic:
                  - list:
                    - listitem [ref=f4e215]:
                      - generic "Add to wishlist" [ref=f4e217] [cursor=pointer]
              - generic [ref=f4e219]:
                - generic [ref=f4e220]: "Vendor:"
                - generic [ref=f4e221]: BarberCon
                - heading [level=6] [ref=f4e222]:
                  - link "BarberCon Wax Pot Black" [ref=f4e223]:
                    - /url: /collections/all/products/barbercon-wax-pot-black
                - generic [ref=f4e226]:
                  - generic [ref=f4e227]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f4e228]:
                  - button "Sold out BarberCon Wax Pot Black" [ref=f4e231] [cursor=pointer]:
                    - generic [ref=f4e232]: QUICK ADD
                    - generic [ref=f4e233]: ›
                  - generic [ref=f4e234]: IN STOCK
          - listitem [ref=f4e236]:
            - generic [ref=f4e238]:
              - generic [ref=f4e239]:
                - link [ref=f4e241]:
                  - /url: /products/barbercon-wax-pot-white
                  - img "BarberCon Wax Pot White" [ref=f4e243]
                - generic:
                  - list:
                    - listitem [ref=f4e244]:
                      - generic "Add to wishlist" [ref=f4e246] [cursor=pointer]
              - generic [ref=f4e248]:
                - generic [ref=f4e249]: "Vendor:"
                - generic [ref=f4e250]: BarberCon
                - heading [level=6] [ref=f4e251]:
                  - link "BarberCon Wax Pot White" [ref=f4e252]:
                    - /url: /collections/all/products/barbercon-wax-pot-white
                - generic [ref=f4e255]:
                  - generic [ref=f4e256]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f4e257]:
                  - button "Sold out BarberCon Wax Pot White" [ref=f4e260] [cursor=pointer]:
                    - generic [ref=f4e261]: QUICK ADD
                    - generic [ref=f4e262]: ›
                  - generic [ref=f4e263]: IN STOCK
          - listitem [ref=f4e265]:
            - generic [ref=f4e267]:
              - generic [ref=f4e268]:
                - link [ref=f4e270]:
                  - /url: /products/carbon-comb-abs-70739
                  - img "Carbon Comb ABS-70739" [ref=f4e272]
                - generic:
                  - list:
                    - listitem [ref=f4e273]:
                      - generic "Add to wishlist" [ref=f4e275] [cursor=pointer]
              - generic [ref=f4e277]:
                - generic [ref=f4e278]: "Vendor:"
                - generic [ref=f4e279]: H2B / Generic
                - heading [level=6] [ref=f4e280]:
                  - link "Carbon Comb ABS-70739" [ref=f4e281]:
                    - /url: /collections/all/products/carbon-comb-abs-70739
                - generic [ref=f4e284]:
                  - generic [ref=f4e285]: Regular price
                  - text: $7.23 AUD
                - generic [ref=f4e286]:
                  - button "Sold out Carbon Comb ABS-70739" [ref=f4e289] [cursor=pointer]:
                    - generic [ref=f4e290]: QUICK ADD
                    - generic [ref=f4e291]: ›
                  - generic [ref=f4e292]: IN STOCK
          - listitem [ref=f4e294]:
            - generic [ref=f4e296]:
              - generic [ref=f4e297]:
                - link [ref=f4e299]:
                  - /url: /products/carbon-small-cutting-comb-cfc-08139
                  - img "Carbon Small Cutting Comb CFC-08139" [ref=f4e301]
                - generic:
                  - list:
                    - listitem [ref=f4e302]:
                      - generic "Add to wishlist" [ref=f4e304] [cursor=pointer]
              - generic [ref=f4e306]:
                - generic [ref=f4e307]: "Vendor:"
                - generic [ref=f4e308]: H2B / Generic
                - heading [level=6] [ref=f4e309]:
                  - link "Carbon Small Cutting Comb CFC-08139" [ref=f4e310]:
                    - /url: /collections/all/products/carbon-small-cutting-comb-cfc-08139
                - generic [ref=f4e313]:
                  - generic [ref=f4e314]: Regular price
                  - text: $4.50 AUD
                - generic [ref=f4e315]:
                  - button "Sold out Carbon Small Cutting Comb CFC-08139" [ref=f4e318] [cursor=pointer]:
                    - generic [ref=f4e319]: QUICK ADD
                    - generic [ref=f4e320]: ›
                  - generic [ref=f4e321]: IN STOCK
          - listitem [ref=f4e323]:
            - generic [ref=f4e325]:
              - generic [ref=f4e326]:
                - link [ref=f4e328]:
                  - /url: /products/clippercide-spray-425g
                  - img "Clippercide Spray 425g" [ref=f4e330]
                - generic:
                  - list:
                    - listitem [ref=f4e331]:
                      - generic "Add to wishlist" [ref=f4e333] [cursor=pointer]
              - generic [ref=f4e335]:
                - generic [ref=f4e336]: "Vendor:"
                - generic [ref=f4e337]: Clippercide
                - heading [level=6] [ref=f4e338]:
                  - link "Clippercide Spray 425g" [ref=f4e339]:
                    - /url: /collections/all/products/clippercide-spray-425g
                - generic [ref=f4e342]:
                  - generic [ref=f4e343]: Regular price
                  - text: $18.14 AUD
                - generic [ref=f4e344]:
                  - button "Sold out Clippercide Spray 425g" [ref=f4e347] [cursor=pointer]:
                    - generic [ref=f4e348]: QUICK ADD
                    - generic [ref=f4e349]: ›
                  - generic [ref=f4e350]: IN STOCK
          - listitem [ref=f4e352]:
            - generic [ref=f4e354]:
              - generic [ref=f4e355]:
                - link [ref=f4e357]:
                  - /url: /products/coffee-stirrers-1000pcs
                  - img "Coffee Stirrers 1000pcs" [ref=f4e359]
                - generic:
                  - list:
                    - listitem [ref=f4e360]:
                      - generic "Add to wishlist" [ref=f4e362] [cursor=pointer]
              - generic [ref=f4e364]:
                - generic [ref=f4e365]: "Vendor:"
                - generic [ref=f4e366]: Generic
                - heading [level=6] [ref=f4e367]:
                  - link "Coffee Stirrers 1000pcs" [ref=f4e368]:
                    - /url: /collections/all/products/coffee-stirrers-1000pcs
                - generic [ref=f4e371]:
                  - generic [ref=f4e372]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e373]:
                  - button "Sold out Coffee Stirrers 1000pcs" [ref=f4e376] [cursor=pointer]:
                    - generic [ref=f4e377]: QUICK ADD
                    - generic [ref=f4e378]: ›
                  - generic [ref=f4e379]: IN STOCK
          - listitem [ref=f4e381]:
            - generic [ref=f4e383]:
              - generic [ref=f4e384]:
                - link [ref=f4e386]:
                  - /url: /products/cosma-liquid-styptic-25ml
                  - img "Cosma Liquid Styptic 25ml" [ref=f4e388]
                - generic:
                  - list:
                    - listitem [ref=f4e389]:
                      - generic "Add to wishlist" [ref=f4e391] [cursor=pointer]
              - generic [ref=f4e393]:
                - generic [ref=f4e394]: "Vendor:"
                - generic [ref=f4e395]: Cosma
                - heading [level=6] [ref=f4e396]:
                  - link "Cosma Liquid Styptic 25ml" [ref=f4e397]:
                    - /url: /collections/all/products/cosma-liquid-styptic-25ml
                - generic [ref=f4e400]:
                  - generic [ref=f4e401]: Regular price
                  - text: $10.86 AUD
                - generic [ref=f4e402]:
                  - button "Sold out Cosma Liquid Styptic 25ml" [ref=f4e405] [cursor=pointer]:
                    - generic [ref=f4e406]: QUICK ADD
                    - generic [ref=f4e407]: ›
                  - generic [ref=f4e408]: IN STOCK
          - listitem [ref=f4e410]:
            - generic [ref=f4e412]:
              - generic [ref=f4e413]:
                - link [ref=f4e415]:
                  - /url: /products/inca-02-styling-dust-wax-30g
                  - img "INCA 02 Styling Dust Wax 30g" [ref=f4e417]
                - generic:
                  - list:
                    - listitem [ref=f4e418]:
                      - generic "Add to wishlist" [ref=f4e420] [cursor=pointer]
              - generic [ref=f4e422]:
                - generic [ref=f4e423]: "Vendor:"
                - generic [ref=f4e424]: ProRapid
                - heading [level=6] [ref=f4e425]:
                  - link "INCA 02 Styling Dust Wax 30g" [ref=f4e426]:
                    - /url: /collections/all/products/inca-02-styling-dust-wax-30g
                - generic [ref=f4e429]:
                  - generic [ref=f4e430]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e431]:
                  - button "Sold out INCA 02 Styling Dust Wax 30g" [ref=f4e434] [cursor=pointer]:
                    - generic [ref=f4e435]: QUICK ADD
                    - generic [ref=f4e436]: ›
                  - generic [ref=f4e437]: IN STOCK
        - navigation "Pagination" [ref=f4e440]:
          - list [ref=f4e441]:
            - listitem [ref=f4e442]:
              - generic "Page 1" [ref=f4e443]: "1"
            - listitem [ref=f4e444]:
              - link "Page 2" [ref=f4e445] [cursor=pointer]:
                - /url: /collections/all?page=2
                - text: "2"
            - listitem [ref=f4e446]:
              - link "Page 3" [ref=f4e447] [cursor=pointer]:
                - /url: /collections/all?page=3
                - text: "3"
            - listitem [ref=f4e448]:
              - generic [ref=f4e449]: …
            - listitem [ref=f4e450]:
              - link "Page 5" [ref=f4e451] [cursor=pointer]:
                - /url: /collections/all?page=5
                - text: "5"
            - listitem [ref=f4e452]:
              - link "Next page" [ref=f4e453] [cursor=pointer]:
                - /url: /collections/all?page=2
  - link "To top" [ref=f4e456]:
    - /url: "#products"
  - generic [ref=f4e462]:
    - link "Home" [ref=f4e463] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f4e468] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f4e473] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f4e478] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgyOTQ3LCJuYmYiOjE3OTI1NzgxNDd9._K79rjPN5Fo3ss6RFBQA_-C6kH0NOnu_q-5v7rdv6Ek
```

# Test source

```ts
  1  | import { Page, expect } from '@playwright/test';
  2  | 
  3  | /** Opens a real product page, either from PRODUCT_URL env var or the first product on /collections/all. */
  4  | export async function openFirstProduct(page: Page) {
  5  |   if (process.env.PRODUCT_URL) {
  6  |     await page.goto(process.env.PRODUCT_URL);
  7  |     return;
  8  |   }
> 9  |   await page.goto('/collections/all');
     |              ^ Error: page.goto: Test timeout of 30000ms exceeded.
  10 |   const firstProductLink = page.locator('a[href*="/products/"]').first();
  11 |   await expect(firstProductLink, 'expected at least one product on /collections/all').toBeVisible();
  12 |   await firstProductLink.click();
  13 |   await page.waitForLoadState('networkidle');
  14 | }
  15 | 
  16 | /** Opens a real category/collection page, either from CATEGORY_URL env var or the first link under /collections. */
  17 | export async function openFirstCategory(page: Page) {
  18 |   if (process.env.CATEGORY_URL) {
  19 |     await page.goto(process.env.CATEGORY_URL);
  20 |     return;
  21 |   }
  22 |   await page.goto('/collections');
  23 |   const firstCollectionLink = page.locator('a[href*="/collections/"]').first();
  24 |   await expect(firstCollectionLink, 'expected at least one collection link on /collections').toBeVisible();
  25 |   await firstCollectionLink.click();
  26 |   await page.waitForLoadState('networkidle');
  27 | }
  28 | 
  29 | /** Opens a product and adds it to cart, leaving the browser on that product page afterwards. */
  30 | export async function addFirstProductToCart(page: Page, qty?: string) {
  31 |   await openFirstProduct(page);
  32 |   const qtyInput = page.locator('input[type="number"][name="quantity"], input[name="quantity"]').first();
  33 |   if (qty && (await qtyInput.isVisible().catch(() => false))) {
  34 |     await qtyInput.fill(qty);
  35 |   }
  36 |   const addButton = page.getByRole('button', { name: /add to cart/i });
  37 |   await addButton.click();
  38 |   await page.waitForTimeout(1000);
  39 | }
  40 | 
  41 | export function cartLineItems(page: Page) {
  42 |   return page.locator('[class*="cart-item"], [class*="line-item"], tr[class*="cart"]');
  43 | }
  44 | 
  45 | export function couponInput(page: Page) {
  46 |   return page.getByPlaceholder(/discount|coupon|promo/i).first();
  47 | }
  48 | 
  49 | export function quantityInput(page: Page) {
  50 |   return page.locator('input[type="number"][name="quantity"], input[name="quantity"]').first();
  51 | }
  52 | 
```