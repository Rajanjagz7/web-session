# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-details.spec.ts >> Product page — details (PD-01..PD-05) >> PD-04 a single-variant product does not render an empty/broken variant dropdown
- Location: tests\product-details.spec.ts:36:7

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
- generic [active] [ref=f5e1]:
  - banner [ref=f5e5]:
    - generic [ref=f5e8]:
      - group [ref=f5e10]:
        - button "Menu" [ref=f5e11] [cursor=pointer]
      - heading [level=1] [ref=f5e14]:
        - link [ref=f5e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f5e16]
      - generic [ref=f5e17]:
        - generic [ref=f5e18] [cursor=pointer]
        - link [ref=f5e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f5e25] [cursor=pointer]
  - main [ref=f5e32]:
    - navigation "breadcrumbs collection" [ref=f5e37]:
      - link "Home" [ref=f5e38]:
        - /url: /
      - link "All collections" [ref=f5e42]:
        - /url: /collections
      - generic [ref=f5e46]: Products
    - generic [ref=f5e50]:
      - img "Products" [ref=f5e52]
      - generic [ref=f5e54]:
        - heading "Products" [level=2] [ref=f5e55]
        - generic [ref=f5e56]: 52 PRODUCTS
    - generic [ref=f5e60]:
      - complementary "Filter:" [ref=f5e61]:
        - generic [ref=f5e63]:
          - group [ref=f5e65]:
            - generic "Filter and sort" [ref=f5e66] [cursor=pointer]
            - group:
              - button "Price" [ref=f5e70] [cursor=pointer]
            - group:
              - button "Product type" [ref=f5e74] [cursor=pointer]
            - group:
              - button "Availability" [ref=f5e78] [cursor=pointer]
            - group:
              - button "Brand" [ref=f5e82] [cursor=pointer]
            - option "Featured"
            - option "Most relevant"
            - option "Best selling"
            - option "Alphabetically, A-Z" [selected]
            - option "Alphabetically, Z-A"
            - option "Price, low to high"
            - option "Price, high to low"
            - option "Date, old to new"
            - option "Date, new to old"
          - status [ref=f5e86]:
            - heading "52 products" [level=2] [ref=f5e87]
      - generic [ref=f5e89]:
        - list [ref=f5e90]:
          - listitem [ref=f5e91]:
            - generic [ref=f5e93]:
              - generic [ref=f5e94]:
                - link [ref=f5e96]:
                  - /url: /products/andis-clipper-oil-118ml
                  - img "Andis Clipper Oil 118ml" [ref=f5e98]
                - generic:
                  - list:
                    - listitem [ref=f5e99]:
                      - generic "Add to wishlist" [ref=f5e101] [cursor=pointer]
              - generic [ref=f5e103]:
                - generic [ref=f5e104]: "Vendor:"
                - generic [ref=f5e105]: Andis
                - heading [level=6] [ref=f5e106]:
                  - link "Andis Clipper Oil 118ml" [ref=f5e107]:
                    - /url: /collections/all/products/andis-clipper-oil-118ml
                - generic [ref=f5e110]:
                  - generic [ref=f5e111]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f5e112]:
                  - button "Sold out Andis Clipper Oil 118ml" [ref=f5e115] [cursor=pointer]:
                    - generic [ref=f5e116]: QUICK ADD
                    - generic [ref=f5e117]: ›
                  - generic [ref=f5e118]: IN STOCK
          - listitem [ref=f5e120]:
            - generic [ref=f5e122]:
              - generic [ref=f5e123]:
                - link [ref=f5e125]:
                  - /url: /products/astra-blades-green-platinum
                  - img "Astra Green Platinum blade packaging" [ref=f5e127]
                - generic:
                  - list:
                    - listitem [ref=f5e128]:
                      - generic "Add to wishlist" [ref=f5e130] [cursor=pointer]
              - generic [ref=f5e132]:
                - generic [ref=f5e133]: "Vendor:"
                - generic [ref=f5e134]: Astra
                - heading [level=6] [ref=f5e135]:
                  - link "Astra Blades Green Platinum" [ref=f5e136]:
                    - /url: /collections/all/products/astra-blades-green-platinum
                - generic [ref=f5e139]:
                  - generic [ref=f5e140]: Regular price
                  - text: $14.50 AUD
                - generic [ref=f5e141]:
                  - button "Sold out Astra Blades Green Platinum" [ref=f5e144] [cursor=pointer]:
                    - generic [ref=f5e145]: QUICK ADD
                    - generic [ref=f5e146]: ›
                  - generic [ref=f5e147]: IN STOCK
          - listitem [ref=f5e149]:
            - generic [ref=f5e151]:
              - generic [ref=f5e152]:
                - link [ref=f5e154]:
                  - /url: /products/barbercon-acrylic-sterilizing-jar-1094ml
                  - generic [ref=f5e155]:
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f5e156]
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f5e157]
                - generic:
                  - list:
                    - listitem [ref=f5e158]:
                      - generic "Add to wishlist" [ref=f5e160] [cursor=pointer]
              - generic [ref=f5e162]:
                - generic [ref=f5e163]: "Vendor:"
                - generic [ref=f5e164]: BarberCon
                - heading [level=6] [ref=f5e165]:
                  - link "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f5e166]:
                    - /url: /collections/all/products/barbercon-acrylic-sterilizing-jar-1094ml
                - generic [ref=f5e169]:
                  - generic [ref=f5e170]: Regular price
                  - text: $27.23 AUD
                - generic [ref=f5e171]:
                  - button "Sold out BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f5e174] [cursor=pointer]:
                    - generic [ref=f5e175]: QUICK ADD
                    - generic [ref=f5e176]: ›
                  - generic [ref=f5e177]: IN STOCK
          - listitem [ref=f5e179]:
            - generic [ref=f5e181]:
              - generic [ref=f5e182]:
                - link [ref=f5e184]:
                  - /url: /products/barbercon-neck-strips-white
                  - img "BarberCon Neck Strips - White" [ref=f5e186]
                - generic:
                  - list:
                    - listitem [ref=f5e187]:
                      - generic "Add to wishlist" [ref=f5e189] [cursor=pointer]
              - generic [ref=f5e191]:
                - generic [ref=f5e192]: "Vendor:"
                - generic [ref=f5e193]: BarberCon
                - heading [level=6] [ref=f5e194]:
                  - link "BarberCon Neck Strips - White" [ref=f5e195]:
                    - /url: /collections/all/products/barbercon-neck-strips-white
                - generic [ref=f5e198]:
                  - generic [ref=f5e199]: Regular price
                  - text: $6.32 AUD
                - generic [ref=f5e200]:
                  - button "Sold out BarberCon Neck Strips - White" [ref=f5e203] [cursor=pointer]:
                    - generic [ref=f5e204]: QUICK ADD
                    - generic [ref=f5e205]: ›
                  - generic [ref=f5e206]: IN STOCK
          - listitem [ref=f5e208]:
            - generic [ref=f5e210]:
              - generic [ref=f5e211]:
                - link [ref=f5e213]:
                  - /url: /products/barbercon-wax-pot-black
                  - img "BarberCon Wax Pot Black" [ref=f5e215]
                - generic:
                  - list:
                    - listitem [ref=f5e216]:
                      - generic "Add to wishlist" [ref=f5e218] [cursor=pointer]
              - generic [ref=f5e220]:
                - generic [ref=f5e221]: "Vendor:"
                - generic [ref=f5e222]: BarberCon
                - heading [level=6] [ref=f5e223]:
                  - link "BarberCon Wax Pot Black" [ref=f5e224]:
                    - /url: /collections/all/products/barbercon-wax-pot-black
                - generic [ref=f5e227]:
                  - generic [ref=f5e228]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f5e229]:
                  - button "Sold out BarberCon Wax Pot Black" [ref=f5e232] [cursor=pointer]:
                    - generic [ref=f5e233]: QUICK ADD
                    - generic [ref=f5e234]: ›
                  - generic [ref=f5e235]: IN STOCK
          - listitem [ref=f5e237]:
            - generic [ref=f5e239]:
              - generic [ref=f5e240]:
                - link [ref=f5e242]:
                  - /url: /products/barbercon-wax-pot-white
                  - img "BarberCon Wax Pot White" [ref=f5e244]
                - generic:
                  - list:
                    - listitem [ref=f5e245]:
                      - generic "Add to wishlist" [ref=f5e247] [cursor=pointer]
              - generic [ref=f5e249]:
                - generic [ref=f5e250]: "Vendor:"
                - generic [ref=f5e251]: BarberCon
                - heading [level=6] [ref=f5e252]:
                  - link "BarberCon Wax Pot White" [ref=f5e253]:
                    - /url: /collections/all/products/barbercon-wax-pot-white
                - generic [ref=f5e256]:
                  - generic [ref=f5e257]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f5e258]:
                  - button "Sold out BarberCon Wax Pot White" [ref=f5e261] [cursor=pointer]:
                    - generic [ref=f5e262]: QUICK ADD
                    - generic [ref=f5e263]: ›
                  - generic [ref=f5e264]: IN STOCK
          - listitem [ref=f5e266]:
            - generic [ref=f5e268]:
              - generic [ref=f5e269]:
                - link [ref=f5e271]:
                  - /url: /products/carbon-comb-abs-70739
                  - img "Carbon Comb ABS-70739" [ref=f5e273]
                - generic:
                  - list:
                    - listitem [ref=f5e274]:
                      - generic "Add to wishlist" [ref=f5e276] [cursor=pointer]
              - generic [ref=f5e278]:
                - generic [ref=f5e279]: "Vendor:"
                - generic [ref=f5e280]: H2B / Generic
                - heading [level=6] [ref=f5e281]:
                  - link "Carbon Comb ABS-70739" [ref=f5e282]:
                    - /url: /collections/all/products/carbon-comb-abs-70739
                - generic [ref=f5e285]:
                  - generic [ref=f5e286]: Regular price
                  - text: $7.23 AUD
                - generic [ref=f5e287]:
                  - button "Sold out Carbon Comb ABS-70739" [ref=f5e290] [cursor=pointer]:
                    - generic [ref=f5e291]: QUICK ADD
                    - generic [ref=f5e292]: ›
                  - generic [ref=f5e293]: IN STOCK
          - listitem [ref=f5e295]:
            - generic [ref=f5e297]:
              - generic [ref=f5e298]:
                - link [ref=f5e300]:
                  - /url: /products/carbon-small-cutting-comb-cfc-08139
                  - img "Carbon Small Cutting Comb CFC-08139" [ref=f5e302]
                - generic:
                  - list:
                    - listitem [ref=f5e303]:
                      - generic "Add to wishlist" [ref=f5e305] [cursor=pointer]
              - generic [ref=f5e307]:
                - generic [ref=f5e308]: "Vendor:"
                - generic [ref=f5e309]: H2B / Generic
                - heading [level=6] [ref=f5e310]:
                  - link "Carbon Small Cutting Comb CFC-08139" [ref=f5e311]:
                    - /url: /collections/all/products/carbon-small-cutting-comb-cfc-08139
                - generic [ref=f5e314]:
                  - generic [ref=f5e315]: Regular price
                  - text: $4.50 AUD
                - generic [ref=f5e316]:
                  - button "Sold out Carbon Small Cutting Comb CFC-08139" [ref=f5e319] [cursor=pointer]:
                    - generic [ref=f5e320]: QUICK ADD
                    - generic [ref=f5e321]: ›
                  - generic [ref=f5e322]: IN STOCK
          - listitem [ref=f5e324]:
            - generic [ref=f5e326]:
              - generic [ref=f5e327]:
                - link [ref=f5e329]:
                  - /url: /products/clippercide-spray-425g
                  - img "Clippercide Spray 425g" [ref=f5e331]
                - generic:
                  - list:
                    - listitem [ref=f5e332]:
                      - generic "Add to wishlist" [ref=f5e334] [cursor=pointer]
              - generic [ref=f5e336]:
                - generic [ref=f5e337]: "Vendor:"
                - generic [ref=f5e338]: Clippercide
                - heading [level=6] [ref=f5e339]:
                  - link "Clippercide Spray 425g" [ref=f5e340]:
                    - /url: /collections/all/products/clippercide-spray-425g
                - generic [ref=f5e343]:
                  - generic [ref=f5e344]: Regular price
                  - text: $18.14 AUD
                - generic [ref=f5e345]:
                  - button "Sold out Clippercide Spray 425g" [ref=f5e348] [cursor=pointer]:
                    - generic [ref=f5e349]: QUICK ADD
                    - generic [ref=f5e350]: ›
                  - generic [ref=f5e351]: IN STOCK
          - listitem [ref=f5e353]:
            - generic [ref=f5e355]:
              - generic [ref=f5e356]:
                - link [ref=f5e358]:
                  - /url: /products/coffee-stirrers-1000pcs
                  - img "Coffee Stirrers 1000pcs" [ref=f5e360]
                - generic:
                  - list:
                    - listitem [ref=f5e361]:
                      - generic "Add to wishlist" [ref=f5e363] [cursor=pointer]
              - generic [ref=f5e365]:
                - generic [ref=f5e366]: "Vendor:"
                - generic [ref=f5e367]: Generic
                - heading [level=6] [ref=f5e368]:
                  - link "Coffee Stirrers 1000pcs" [ref=f5e369]:
                    - /url: /collections/all/products/coffee-stirrers-1000pcs
                - generic [ref=f5e372]:
                  - generic [ref=f5e373]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f5e374]:
                  - button "Sold out Coffee Stirrers 1000pcs" [ref=f5e377] [cursor=pointer]:
                    - generic [ref=f5e378]: QUICK ADD
                    - generic [ref=f5e379]: ›
                  - generic [ref=f5e380]: IN STOCK
          - listitem [ref=f5e382]:
            - generic [ref=f5e384]:
              - generic [ref=f5e385]:
                - link [ref=f5e387]:
                  - /url: /products/cosma-liquid-styptic-25ml
                  - img "Cosma Liquid Styptic 25ml" [ref=f5e389]
                - generic:
                  - list:
                    - listitem [ref=f5e390]:
                      - generic "Add to wishlist" [ref=f5e392] [cursor=pointer]
              - generic [ref=f5e394]:
                - generic [ref=f5e395]: "Vendor:"
                - generic [ref=f5e396]: Cosma
                - heading [level=6] [ref=f5e397]:
                  - link "Cosma Liquid Styptic 25ml" [ref=f5e398]:
                    - /url: /collections/all/products/cosma-liquid-styptic-25ml
                - generic [ref=f5e401]:
                  - generic [ref=f5e402]: Regular price
                  - text: $10.86 AUD
                - generic [ref=f5e403]:
                  - button "Sold out Cosma Liquid Styptic 25ml" [ref=f5e406] [cursor=pointer]:
                    - generic [ref=f5e407]: QUICK ADD
                    - generic [ref=f5e408]: ›
                  - generic [ref=f5e409]: IN STOCK
          - listitem [ref=f5e411]:
            - generic [ref=f5e413]:
              - generic [ref=f5e414]:
                - link [ref=f5e416]:
                  - /url: /products/inca-02-styling-dust-wax-30g
                  - img "INCA 02 Styling Dust Wax 30g" [ref=f5e418]
                - generic:
                  - list:
                    - listitem [ref=f5e419]:
                      - generic "Add to wishlist" [ref=f5e421] [cursor=pointer]
              - generic [ref=f5e423]:
                - generic [ref=f5e424]: "Vendor:"
                - generic [ref=f5e425]: ProRapid
                - heading [level=6] [ref=f5e426]:
                  - link "INCA 02 Styling Dust Wax 30g" [ref=f5e427]:
                    - /url: /collections/all/products/inca-02-styling-dust-wax-30g
                - generic [ref=f5e430]:
                  - generic [ref=f5e431]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f5e432]:
                  - button "Sold out INCA 02 Styling Dust Wax 30g" [ref=f5e435] [cursor=pointer]:
                    - generic [ref=f5e436]: QUICK ADD
                    - generic [ref=f5e437]: ›
                  - generic [ref=f5e438]: IN STOCK
        - navigation "Pagination" [ref=f5e441]:
          - list [ref=f5e442]:
            - listitem [ref=f5e443]:
              - generic "Page 1" [ref=f5e444]: "1"
            - listitem [ref=f5e445]:
              - link "Page 2" [ref=f5e446] [cursor=pointer]:
                - /url: /collections/all?page=2
                - text: "2"
            - listitem [ref=f5e447]:
              - link "Page 3" [ref=f5e448] [cursor=pointer]:
                - /url: /collections/all?page=3
                - text: "3"
            - listitem [ref=f5e449]:
              - generic [ref=f5e450]: …
            - listitem [ref=f5e451]:
              - link "Page 5" [ref=f5e452] [cursor=pointer]:
                - /url: /collections/all?page=5
                - text: "5"
            - listitem [ref=f5e453]:
              - link "Next page" [ref=f5e454] [cursor=pointer]:
                - /url: /collections/all?page=2
  - link "To top" [ref=f5e457]:
    - /url: "#products"
  - generic [ref=f5e463]:
    - link "Home" [ref=f5e464] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f5e469] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f5e474] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f5e479] [cursor=pointer]:
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