# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — sidebar display (SC-01..SC-03) >> SC-02 cart with exactly 1 item renders cleanly
- Location: tests\cart.spec.ts:15:7

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
        - generic "Menu" [ref=f4e11] [cursor=pointer]
      - heading [level=1] [ref=f4e14]:
        - link [ref=f4e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f4e16]
      - generic [ref=f4e17]:
        - generic [ref=f4e18] [cursor=pointer]
        - link [ref=f4e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - link [ref=f4e26] [cursor=pointer]:
          - /url: /cart
  - main [ref=f4e33]:
    - navigation "breadcrumbs collection" [ref=f4e38]:
      - link "Home" [ref=f4e39]:
        - /url: /
      - link "All collections" [ref=f4e43]:
        - /url: /collections
      - generic [ref=f4e47]: Products
    - generic [ref=f4e51]:
      - img "Products" [ref=f4e53]
      - generic [ref=f4e55]:
        - heading "Products" [level=2] [ref=f4e56]
        - generic [ref=f4e57]: 52 PRODUCTS
    - generic [ref=f4e61]:
      - complementary "Filter:" [ref=f4e62]:
        - generic [ref=f4e63]:
          - group [ref=f4e65]:
            - generic "Filter and sort" [ref=f4e66] [cursor=pointer]
            - group:
              - generic "Price" [ref=f4e70] [cursor=pointer]
            - group:
              - generic "Product type" [ref=f4e74] [cursor=pointer]
            - group:
              - generic "Availability" [ref=f4e78] [cursor=pointer]
            - group:
              - generic "Brand" [ref=f4e82] [cursor=pointer]
            - option "Featured"
            - option "Most relevant"
            - option "Best selling"
            - option "Alphabetically, A-Z" [selected]
            - option "Alphabetically, Z-A"
            - option "Price, low to high"
            - option "Price, high to low"
            - option "Date, old to new"
            - option "Date, new to old"
          - status [ref=f4e86]:
            - heading "52 products" [level=2] [ref=f4e87]
      - generic [ref=f4e89]:
        - list [ref=f4e90]:
          - listitem [ref=f4e91]:
            - generic [ref=f4e93]:
              - generic [ref=f4e94]:
                - link [ref=f4e96]:
                  - /url: /products/andis-clipper-oil-118ml
                  - img "Andis Clipper Oil 118ml" [ref=f4e98]
                - generic:
                  - list:
                    - listitem [ref=f4e99]:
                      - generic "Add to wishlist" [ref=f4e101] [cursor=pointer]
              - generic [ref=f4e103]:
                - generic [ref=f4e104]: "Vendor:"
                - generic [ref=f4e105]: Andis
                - heading [level=6] [ref=f4e106]:
                  - link "Andis Clipper Oil 118ml" [ref=f4e107]:
                    - /url: /collections/all/products/andis-clipper-oil-118ml
                - generic [ref=f4e110]:
                  - generic [ref=f4e111]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e112]:
                  - button "Sold out Andis Clipper Oil 118ml" [ref=f4e115] [cursor=pointer]:
                    - generic [ref=f4e116]: QUICK ADD
                    - generic [ref=f4e117]: ›
                  - generic [ref=f4e118]: IN STOCK
          - listitem [ref=f4e120]:
            - generic [ref=f4e122]:
              - generic [ref=f4e123]:
                - link [ref=f4e125]:
                  - /url: /products/astra-blades-green-platinum
                  - img "Astra Green Platinum blade packaging" [ref=f4e127]
                - generic:
                  - list:
                    - listitem [ref=f4e128]:
                      - generic "Add to wishlist" [ref=f4e130] [cursor=pointer]
              - generic [ref=f4e132]:
                - generic [ref=f4e133]: "Vendor:"
                - generic [ref=f4e134]: Astra
                - heading [level=6] [ref=f4e135]:
                  - link "Astra Blades Green Platinum" [ref=f4e136]:
                    - /url: /collections/all/products/astra-blades-green-platinum
                - generic [ref=f4e139]:
                  - generic [ref=f4e140]: Regular price
                  - text: $14.50 AUD
                - generic [ref=f4e141]:
                  - button "Sold out Astra Blades Green Platinum" [ref=f4e144] [cursor=pointer]:
                    - generic [ref=f4e145]: QUICK ADD
                    - generic [ref=f4e146]: ›
                  - generic [ref=f4e147]: IN STOCK
          - listitem [ref=f4e149]:
            - generic [ref=f4e151]:
              - generic [ref=f4e152]:
                - link [ref=f4e154]:
                  - /url: /products/barbercon-acrylic-sterilizing-jar-1094ml
                  - generic [ref=f4e155]:
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e156]
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e157]
                - generic:
                  - list:
                    - listitem [ref=f4e158]:
                      - generic "Add to wishlist" [ref=f4e160] [cursor=pointer]
              - generic [ref=f4e162]:
                - generic [ref=f4e163]: "Vendor:"
                - generic [ref=f4e164]: BarberCon
                - heading [level=6] [ref=f4e165]:
                  - link "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e166]:
                    - /url: /collections/all/products/barbercon-acrylic-sterilizing-jar-1094ml
                - generic [ref=f4e169]:
                  - generic [ref=f4e170]: Regular price
                  - text: $27.23 AUD
                - generic [ref=f4e171]:
                  - button "Sold out BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e174] [cursor=pointer]:
                    - generic [ref=f4e175]: QUICK ADD
                    - generic [ref=f4e176]: ›
                  - generic [ref=f4e177]: IN STOCK
          - listitem [ref=f4e179]:
            - generic [ref=f4e181]:
              - generic [ref=f4e182]:
                - link [ref=f4e184]:
                  - /url: /products/barbercon-neck-strips-white
                  - img "BarberCon Neck Strips - White" [ref=f4e186]
                - generic:
                  - list:
                    - listitem [ref=f4e187]:
                      - generic "Add to wishlist" [ref=f4e189] [cursor=pointer]
              - generic [ref=f4e191]:
                - generic [ref=f4e192]: "Vendor:"
                - generic [ref=f4e193]: BarberCon
                - heading [level=6] [ref=f4e194]:
                  - link "BarberCon Neck Strips - White" [ref=f4e195]:
                    - /url: /collections/all/products/barbercon-neck-strips-white
                - generic [ref=f4e198]:
                  - generic [ref=f4e199]: Regular price
                  - text: $6.32 AUD
                - generic [ref=f4e200]:
                  - button "Sold out BarberCon Neck Strips - White" [ref=f4e203] [cursor=pointer]:
                    - generic [ref=f4e204]: QUICK ADD
                    - generic [ref=f4e205]: ›
                  - generic [ref=f4e206]: IN STOCK
          - listitem [ref=f4e208]:
            - generic [ref=f4e210]:
              - generic [ref=f4e211]:
                - link [ref=f4e213]:
                  - /url: /products/barbercon-wax-pot-black
                  - img "BarberCon Wax Pot Black" [ref=f4e215]
                - generic:
                  - list:
                    - listitem [ref=f4e216]:
                      - generic "Add to wishlist" [ref=f4e218] [cursor=pointer]
              - generic [ref=f4e220]:
                - generic [ref=f4e221]: "Vendor:"
                - generic [ref=f4e222]: BarberCon
                - heading [level=6] [ref=f4e223]:
                  - link "BarberCon Wax Pot Black" [ref=f4e224]:
                    - /url: /collections/all/products/barbercon-wax-pot-black
                - generic [ref=f4e227]:
                  - generic [ref=f4e228]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f4e229]:
                  - button "Sold out BarberCon Wax Pot Black" [ref=f4e232] [cursor=pointer]:
                    - generic [ref=f4e233]: QUICK ADD
                    - generic [ref=f4e234]: ›
                  - generic [ref=f4e235]: IN STOCK
          - listitem [ref=f4e237]:
            - generic [ref=f4e239]:
              - generic [ref=f4e240]:
                - link [ref=f4e242]:
                  - /url: /products/barbercon-wax-pot-white
                  - img "BarberCon Wax Pot White" [ref=f4e244]
                - generic:
                  - list:
                    - listitem [ref=f4e245]:
                      - generic "Add to wishlist" [ref=f4e247] [cursor=pointer]
              - generic [ref=f4e249]:
                - generic [ref=f4e250]: "Vendor:"
                - generic [ref=f4e251]: BarberCon
                - heading [level=6] [ref=f4e252]:
                  - link "BarberCon Wax Pot White" [ref=f4e253]:
                    - /url: /collections/all/products/barbercon-wax-pot-white
                - generic [ref=f4e256]:
                  - generic [ref=f4e257]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f4e258]:
                  - button "Sold out BarberCon Wax Pot White" [ref=f4e261] [cursor=pointer]:
                    - generic [ref=f4e262]: QUICK ADD
                    - generic [ref=f4e263]: ›
                  - generic [ref=f4e264]: IN STOCK
          - listitem [ref=f4e266]:
            - generic [ref=f4e268]:
              - generic [ref=f4e269]:
                - link [ref=f4e271]:
                  - /url: /products/carbon-comb-abs-70739
                  - img "Carbon Comb ABS-70739" [ref=f4e273]
                - generic:
                  - list:
                    - listitem [ref=f4e274]:
                      - generic "Add to wishlist" [ref=f4e276] [cursor=pointer]
              - generic [ref=f4e278]:
                - generic [ref=f4e279]: "Vendor:"
                - generic [ref=f4e280]: H2B / Generic
                - heading [level=6] [ref=f4e281]:
                  - link "Carbon Comb ABS-70739" [ref=f4e282]:
                    - /url: /collections/all/products/carbon-comb-abs-70739
                - generic [ref=f4e285]:
                  - generic [ref=f4e286]: Regular price
                  - text: $7.23 AUD
                - generic [ref=f4e287]:
                  - button "Sold out Carbon Comb ABS-70739" [ref=f4e290] [cursor=pointer]:
                    - generic [ref=f4e291]: QUICK ADD
                    - generic [ref=f4e292]: ›
                  - generic [ref=f4e293]: IN STOCK
          - listitem [ref=f4e295]:
            - generic [ref=f4e297]:
              - generic [ref=f4e298]:
                - link [ref=f4e300]:
                  - /url: /products/carbon-small-cutting-comb-cfc-08139
                  - img "Carbon Small Cutting Comb CFC-08139" [ref=f4e302]
                - generic:
                  - list:
                    - listitem [ref=f4e303]:
                      - generic "Add to wishlist" [ref=f4e305] [cursor=pointer]
              - generic [ref=f4e307]:
                - generic [ref=f4e308]: "Vendor:"
                - generic [ref=f4e309]: H2B / Generic
                - heading [level=6] [ref=f4e310]:
                  - link "Carbon Small Cutting Comb CFC-08139" [ref=f4e311]:
                    - /url: /collections/all/products/carbon-small-cutting-comb-cfc-08139
                - generic [ref=f4e314]:
                  - generic [ref=f4e315]: Regular price
                  - text: $4.50 AUD
                - generic [ref=f4e316]:
                  - button "Sold out Carbon Small Cutting Comb CFC-08139" [ref=f4e319] [cursor=pointer]:
                    - generic [ref=f4e320]: QUICK ADD
                    - generic [ref=f4e321]: ›
                  - generic [ref=f4e322]: IN STOCK
          - listitem [ref=f4e324]:
            - generic [ref=f4e326]:
              - generic [ref=f4e327]:
                - link [ref=f4e329]:
                  - /url: /products/clippercide-spray-425g
                  - img "Clippercide Spray 425g" [ref=f4e331]
                - generic:
                  - list:
                    - listitem [ref=f4e332]:
                      - generic "Add to wishlist" [ref=f4e334] [cursor=pointer]
              - generic [ref=f4e336]:
                - generic [ref=f4e337]: "Vendor:"
                - generic [ref=f4e338]: Clippercide
                - heading [level=6] [ref=f4e339]:
                  - link "Clippercide Spray 425g" [ref=f4e340]:
                    - /url: /collections/all/products/clippercide-spray-425g
                - generic [ref=f4e343]:
                  - generic [ref=f4e344]: Regular price
                  - text: $18.14 AUD
                - generic [ref=f4e345]:
                  - button "Sold out Clippercide Spray 425g" [ref=f4e348] [cursor=pointer]:
                    - generic [ref=f4e349]: QUICK ADD
                    - generic [ref=f4e350]: ›
                  - generic [ref=f4e351]: IN STOCK
          - listitem [ref=f4e353]:
            - generic [ref=f4e355]:
              - generic [ref=f4e356]:
                - link [ref=f4e358]:
                  - /url: /products/coffee-stirrers-1000pcs
                  - img "Coffee Stirrers 1000pcs" [ref=f4e360]
                - generic:
                  - list:
                    - listitem [ref=f4e361]:
                      - generic "Add to wishlist" [ref=f4e363] [cursor=pointer]
              - generic [ref=f4e365]:
                - generic [ref=f4e366]: "Vendor:"
                - generic [ref=f4e367]: Generic
                - heading [level=6] [ref=f4e368]:
                  - link "Coffee Stirrers 1000pcs" [ref=f4e369]:
                    - /url: /collections/all/products/coffee-stirrers-1000pcs
                - generic [ref=f4e372]:
                  - generic [ref=f4e373]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e374]:
                  - button "Sold out Coffee Stirrers 1000pcs" [ref=f4e377] [cursor=pointer]:
                    - generic [ref=f4e378]: QUICK ADD
                    - generic [ref=f4e379]: ›
                  - generic [ref=f4e380]: IN STOCK
          - listitem [ref=f4e382]:
            - generic [ref=f4e384]:
              - generic [ref=f4e385]:
                - link [ref=f4e387]:
                  - /url: /products/cosma-liquid-styptic-25ml
                  - img "Cosma Liquid Styptic 25ml" [ref=f4e389]
                - generic:
                  - list:
                    - listitem [ref=f4e390]:
                      - generic "Add to wishlist" [ref=f4e392] [cursor=pointer]
              - generic [ref=f4e394]:
                - generic [ref=f4e395]: "Vendor:"
                - generic [ref=f4e396]: Cosma
                - heading [level=6] [ref=f4e397]:
                  - link "Cosma Liquid Styptic 25ml" [ref=f4e398]:
                    - /url: /collections/all/products/cosma-liquid-styptic-25ml
                - generic [ref=f4e401]:
                  - generic [ref=f4e402]: Regular price
                  - text: $10.86 AUD
                - generic [ref=f4e403]:
                  - button "Sold out Cosma Liquid Styptic 25ml" [ref=f4e406] [cursor=pointer]:
                    - generic [ref=f4e407]: QUICK ADD
                    - generic [ref=f4e408]: ›
                  - generic [ref=f4e409]: IN STOCK
          - listitem [ref=f4e411]:
            - generic [ref=f4e413]:
              - generic [ref=f4e414]:
                - link [ref=f4e416]:
                  - /url: /products/inca-02-styling-dust-wax-30g
                  - img "INCA 02 Styling Dust Wax 30g" [ref=f4e418]
                - generic:
                  - list:
                    - listitem [ref=f4e419]:
                      - generic "Add to wishlist" [ref=f4e421] [cursor=pointer]
              - generic [ref=f4e423]:
                - generic [ref=f4e424]: "Vendor:"
                - generic [ref=f4e425]: ProRapid
                - heading [level=6] [ref=f4e426]:
                  - link "INCA 02 Styling Dust Wax 30g" [ref=f4e427]:
                    - /url: /collections/all/products/inca-02-styling-dust-wax-30g
                - generic [ref=f4e430]:
                  - generic [ref=f4e431]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e432]:
                  - button "Sold out INCA 02 Styling Dust Wax 30g" [ref=f4e435] [cursor=pointer]:
                    - generic [ref=f4e436]: QUICK ADD
                    - generic [ref=f4e437]: ›
                  - generic [ref=f4e438]: IN STOCK
        - navigation "Pagination" [ref=f4e441]:
          - list [ref=f4e442]:
            - listitem [ref=f4e443]:
              - generic "Page 1" [ref=f4e444]: "1"
            - listitem [ref=f4e445]:
              - link "Page 2" [ref=f4e446] [cursor=pointer]:
                - /url: /collections/all?page=2
                - text: "2"
            - listitem [ref=f4e447]:
              - link "Page 3" [ref=f4e448] [cursor=pointer]:
                - /url: /collections/all?page=3
                - text: "3"
            - listitem [ref=f4e449]:
              - generic [ref=f4e450]: …
            - listitem [ref=f4e451]:
              - link "Page 5" [ref=f4e452] [cursor=pointer]:
                - /url: /collections/all?page=5
                - text: "5"
            - listitem [ref=f4e453]:
              - link "Next page" [ref=f4e454] [cursor=pointer]:
                - /url: /collections/all?page=2
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