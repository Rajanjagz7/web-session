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
        - link [ref=f5e32] [cursor=pointer]:
          - /url: /account
  - main [ref=f5e36]:
    - navigation "breadcrumbs collection" [ref=f5e41]:
      - link "Home" [ref=f5e42]:
        - /url: /
      - link "All collections" [ref=f5e46]:
        - /url: /collections
      - generic [ref=f5e50]: Products
    - generic [ref=f5e54]:
      - img "Products" [ref=f5e56]
      - generic [ref=f5e58]:
        - heading "Products" [level=2] [ref=f5e59]
        - generic [ref=f5e60]: 52 PRODUCTS
    - generic [ref=f5e64]:
      - complementary "Filter:" [ref=f5e65]:
        - generic [ref=f5e66]:
          - group [ref=f5e68]:
            - generic "Filter and sort" [ref=f5e69] [cursor=pointer]
            - group:
              - button "Price" [ref=f5e73] [cursor=pointer]
            - group:
              - button "Product type" [ref=f5e77] [cursor=pointer]
            - group:
              - button "Availability" [ref=f5e81] [cursor=pointer]
            - group:
              - button "Brand" [ref=f5e85] [cursor=pointer]
            - option "Featured"
            - option "Most relevant"
            - option "Best selling"
            - option "Alphabetically, A-Z" [selected]
            - option "Alphabetically, Z-A"
            - option "Price, low to high"
            - option "Price, high to low"
            - option "Date, old to new"
            - option "Date, new to old"
          - status [ref=f5e89]:
            - heading "52 products" [level=2] [ref=f5e90]
      - generic [ref=f5e92]:
        - list [ref=f5e93]:
          - listitem [ref=f5e94]:
            - generic [ref=f5e96]:
              - generic [ref=f5e97]:
                - link [ref=f5e99]:
                  - /url: /products/andis-clipper-oil-118ml
                  - img "Andis Clipper Oil 118ml" [ref=f5e101]
                - generic:
                  - list:
                    - listitem [ref=f5e102]:
                      - generic "Add to wishlist" [ref=f5e104] [cursor=pointer]
              - generic [ref=f5e106]:
                - generic [ref=f5e107]: "Vendor:"
                - generic [ref=f5e108]: Andis
                - heading [level=6] [ref=f5e109]:
                  - link "Andis Clipper Oil 118ml" [ref=f5e110]:
                    - /url: /collections/all/products/andis-clipper-oil-118ml
                - generic [ref=f5e113]:
                  - generic [ref=f5e114]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f5e115]:
                  - button "Sold out Andis Clipper Oil 118ml" [ref=f5e118] [cursor=pointer]:
                    - generic [ref=f5e119]: QUICK ADD
                    - generic [ref=f5e120]: ›
                  - generic [ref=f5e121]: IN STOCK
          - listitem [ref=f5e123]:
            - generic [ref=f5e125]:
              - generic [ref=f5e126]:
                - link [ref=f5e128]:
                  - /url: /products/astra-blades-green-platinum
                  - img "Astra Green Platinum blade packaging" [ref=f5e130]
                - generic:
                  - list:
                    - listitem [ref=f5e131]:
                      - generic "Add to wishlist" [ref=f5e133] [cursor=pointer]
              - generic [ref=f5e135]:
                - generic [ref=f5e136]: "Vendor:"
                - generic [ref=f5e137]: Astra
                - heading [level=6] [ref=f5e138]:
                  - link "Astra Blades Green Platinum" [ref=f5e139]:
                    - /url: /collections/all/products/astra-blades-green-platinum
                - generic [ref=f5e142]:
                  - generic [ref=f5e143]: Regular price
                  - text: $14.50 AUD
                - generic [ref=f5e144]:
                  - button "Sold out Astra Blades Green Platinum" [ref=f5e147] [cursor=pointer]:
                    - generic [ref=f5e148]: QUICK ADD
                    - generic [ref=f5e149]: ›
                  - generic [ref=f5e150]: IN STOCK
          - listitem [ref=f5e152]:
            - generic [ref=f5e154]:
              - generic [ref=f5e155]:
                - link [ref=f5e157]:
                  - /url: /products/barbercon-acrylic-sterilizing-jar-1094ml
                  - generic [ref=f5e158]:
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f5e159]
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f5e160]
                - generic:
                  - list:
                    - listitem [ref=f5e161]:
                      - generic "Add to wishlist" [ref=f5e163] [cursor=pointer]
              - generic [ref=f5e165]:
                - generic [ref=f5e166]: "Vendor:"
                - generic [ref=f5e167]: BarberCon
                - heading [level=6] [ref=f5e168]:
                  - link "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f5e169]:
                    - /url: /collections/all/products/barbercon-acrylic-sterilizing-jar-1094ml
                - generic [ref=f5e172]:
                  - generic [ref=f5e173]: Regular price
                  - text: $27.23 AUD
                - generic [ref=f5e174]:
                  - button "Sold out BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f5e177] [cursor=pointer]:
                    - generic [ref=f5e178]: QUICK ADD
                    - generic [ref=f5e179]: ›
                  - generic [ref=f5e180]: IN STOCK
          - listitem [ref=f5e182]:
            - generic [ref=f5e184]:
              - generic [ref=f5e185]:
                - link [ref=f5e187]:
                  - /url: /products/barbercon-neck-strips-white
                  - img "BarberCon Neck Strips - White" [ref=f5e189]
                - generic:
                  - list:
                    - listitem [ref=f5e190]:
                      - generic "Add to wishlist" [ref=f5e192] [cursor=pointer]
              - generic [ref=f5e194]:
                - generic [ref=f5e195]: "Vendor:"
                - generic [ref=f5e196]: BarberCon
                - heading [level=6] [ref=f5e197]:
                  - link "BarberCon Neck Strips - White" [ref=f5e198]:
                    - /url: /collections/all/products/barbercon-neck-strips-white
                - generic [ref=f5e201]:
                  - generic [ref=f5e202]: Regular price
                  - text: $6.32 AUD
                - generic [ref=f5e203]:
                  - button "Sold out BarberCon Neck Strips - White" [ref=f5e206] [cursor=pointer]:
                    - generic [ref=f5e207]: QUICK ADD
                    - generic [ref=f5e208]: ›
                  - generic [ref=f5e209]: IN STOCK
          - listitem [ref=f5e211]:
            - generic [ref=f5e213]:
              - generic [ref=f5e214]:
                - link [ref=f5e216]:
                  - /url: /products/barbercon-wax-pot-black
                  - img "BarberCon Wax Pot Black" [ref=f5e218]
                - generic:
                  - list:
                    - listitem [ref=f5e219]:
                      - generic "Add to wishlist" [ref=f5e221] [cursor=pointer]
              - generic [ref=f5e223]:
                - generic [ref=f5e224]: "Vendor:"
                - generic [ref=f5e225]: BarberCon
                - heading [level=6] [ref=f5e226]:
                  - link "BarberCon Wax Pot Black" [ref=f5e227]:
                    - /url: /collections/all/products/barbercon-wax-pot-black
                - generic [ref=f5e230]:
                  - generic [ref=f5e231]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f5e232]:
                  - button "Sold out BarberCon Wax Pot Black" [ref=f5e235] [cursor=pointer]:
                    - generic [ref=f5e236]: QUICK ADD
                    - generic [ref=f5e237]: ›
                  - generic [ref=f5e238]: IN STOCK
          - listitem [ref=f5e240]:
            - generic [ref=f5e242]:
              - generic [ref=f5e243]:
                - link [ref=f5e245]:
                  - /url: /products/barbercon-wax-pot-white
                  - img "BarberCon Wax Pot White" [ref=f5e247]
                - generic:
                  - list:
                    - listitem [ref=f5e248]:
                      - generic "Add to wishlist" [ref=f5e250] [cursor=pointer]
              - generic [ref=f5e252]:
                - generic [ref=f5e253]: "Vendor:"
                - generic [ref=f5e254]: BarberCon
                - heading [level=6] [ref=f5e255]:
                  - link "BarberCon Wax Pot White" [ref=f5e256]:
                    - /url: /collections/all/products/barbercon-wax-pot-white
                - generic [ref=f5e259]:
                  - generic [ref=f5e260]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f5e261]:
                  - button "Sold out BarberCon Wax Pot White" [ref=f5e264] [cursor=pointer]:
                    - generic [ref=f5e265]: QUICK ADD
                    - generic [ref=f5e266]: ›
                  - generic [ref=f5e267]: IN STOCK
          - listitem [ref=f5e269]:
            - generic [ref=f5e271]:
              - generic [ref=f5e272]:
                - link [ref=f5e274]:
                  - /url: /products/carbon-comb-abs-70739
                  - img "Carbon Comb ABS-70739" [ref=f5e276]
                - generic:
                  - list:
                    - listitem [ref=f5e277]:
                      - generic "Add to wishlist" [ref=f5e279] [cursor=pointer]
              - generic [ref=f5e281]:
                - generic [ref=f5e282]: "Vendor:"
                - generic [ref=f5e283]: H2B / Generic
                - heading [level=6] [ref=f5e284]:
                  - link "Carbon Comb ABS-70739" [ref=f5e285]:
                    - /url: /collections/all/products/carbon-comb-abs-70739
                - generic [ref=f5e288]:
                  - generic [ref=f5e289]: Regular price
                  - text: $7.23 AUD
                - generic [ref=f5e290]:
                  - button "Sold out Carbon Comb ABS-70739" [ref=f5e293] [cursor=pointer]:
                    - generic [ref=f5e294]: QUICK ADD
                    - generic [ref=f5e295]: ›
                  - generic [ref=f5e296]: IN STOCK
          - listitem [ref=f5e298]:
            - generic [ref=f5e300]:
              - generic [ref=f5e301]:
                - link [ref=f5e303]:
                  - /url: /products/carbon-small-cutting-comb-cfc-08139
                  - img "Carbon Small Cutting Comb CFC-08139" [ref=f5e305]
                - generic:
                  - list:
                    - listitem [ref=f5e306]:
                      - generic "Add to wishlist" [ref=f5e308] [cursor=pointer]
              - generic [ref=f5e310]:
                - generic [ref=f5e311]: "Vendor:"
                - generic [ref=f5e312]: H2B / Generic
                - heading [level=6] [ref=f5e313]:
                  - link "Carbon Small Cutting Comb CFC-08139" [ref=f5e314]:
                    - /url: /collections/all/products/carbon-small-cutting-comb-cfc-08139
                - generic [ref=f5e317]:
                  - generic [ref=f5e318]: Regular price
                  - text: $4.50 AUD
                - generic [ref=f5e319]:
                  - button "Sold out Carbon Small Cutting Comb CFC-08139" [ref=f5e322] [cursor=pointer]:
                    - generic [ref=f5e323]: QUICK ADD
                    - generic [ref=f5e324]: ›
                  - generic [ref=f5e325]: IN STOCK
          - listitem [ref=f5e327]:
            - generic [ref=f5e329]:
              - generic [ref=f5e330]:
                - link [ref=f5e332]:
                  - /url: /products/clippercide-spray-425g
                  - img "Clippercide Spray 425g" [ref=f5e334]
                - generic:
                  - list:
                    - listitem [ref=f5e335]:
                      - generic "Add to wishlist" [ref=f5e337] [cursor=pointer]
              - generic [ref=f5e339]:
                - generic [ref=f5e340]: "Vendor:"
                - generic [ref=f5e341]: Clippercide
                - heading [level=6] [ref=f5e342]:
                  - link "Clippercide Spray 425g" [ref=f5e343]:
                    - /url: /collections/all/products/clippercide-spray-425g
                - generic [ref=f5e346]:
                  - generic [ref=f5e347]: Regular price
                  - text: $18.14 AUD
                - generic [ref=f5e348]:
                  - button "Sold out Clippercide Spray 425g" [ref=f5e351] [cursor=pointer]:
                    - generic [ref=f5e352]: QUICK ADD
                    - generic [ref=f5e353]: ›
                  - generic [ref=f5e354]: IN STOCK
          - listitem [ref=f5e356]:
            - generic [ref=f5e358]:
              - generic [ref=f5e359]:
                - link [ref=f5e361]:
                  - /url: /products/coffee-stirrers-1000pcs
                  - img "Coffee Stirrers 1000pcs" [ref=f5e363]
                - generic:
                  - list:
                    - listitem [ref=f5e364]:
                      - generic "Add to wishlist" [ref=f5e366] [cursor=pointer]
              - generic [ref=f5e368]:
                - generic [ref=f5e369]: "Vendor:"
                - generic [ref=f5e370]: Generic
                - heading [level=6] [ref=f5e371]:
                  - link "Coffee Stirrers 1000pcs" [ref=f5e372]:
                    - /url: /collections/all/products/coffee-stirrers-1000pcs
                - generic [ref=f5e375]:
                  - generic [ref=f5e376]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f5e377]:
                  - button "Sold out Coffee Stirrers 1000pcs" [ref=f5e380] [cursor=pointer]:
                    - generic [ref=f5e381]: QUICK ADD
                    - generic [ref=f5e382]: ›
                  - generic [ref=f5e383]: IN STOCK
          - listitem [ref=f5e385]:
            - generic [ref=f5e387]:
              - generic [ref=f5e388]:
                - link [ref=f5e390]:
                  - /url: /products/cosma-liquid-styptic-25ml
                  - img "Cosma Liquid Styptic 25ml" [ref=f5e392]
                - generic:
                  - list:
                    - listitem [ref=f5e393]:
                      - generic "Add to wishlist" [ref=f5e395] [cursor=pointer]
              - generic [ref=f5e397]:
                - generic [ref=f5e398]: "Vendor:"
                - generic [ref=f5e399]: Cosma
                - heading [level=6] [ref=f5e400]:
                  - link "Cosma Liquid Styptic 25ml" [ref=f5e401]:
                    - /url: /collections/all/products/cosma-liquid-styptic-25ml
                - generic [ref=f5e404]:
                  - generic [ref=f5e405]: Regular price
                  - text: $10.86 AUD
                - generic [ref=f5e406]:
                  - button "Sold out Cosma Liquid Styptic 25ml" [ref=f5e409] [cursor=pointer]:
                    - generic [ref=f5e410]: QUICK ADD
                    - generic [ref=f5e411]: ›
                  - generic [ref=f5e412]: IN STOCK
          - listitem [ref=f5e414]:
            - generic [ref=f5e416]:
              - generic [ref=f5e417]:
                - link [ref=f5e419]:
                  - /url: /products/inca-02-styling-dust-wax-30g
                  - img "INCA 02 Styling Dust Wax 30g" [ref=f5e421]
                - generic:
                  - list:
                    - listitem [ref=f5e422]:
                      - generic "Add to wishlist" [ref=f5e424] [cursor=pointer]
              - generic [ref=f5e426]:
                - generic [ref=f5e427]: "Vendor:"
                - generic [ref=f5e428]: ProRapid
                - heading [level=6] [ref=f5e429]:
                  - link "INCA 02 Styling Dust Wax 30g" [ref=f5e430]:
                    - /url: /collections/all/products/inca-02-styling-dust-wax-30g
                - generic [ref=f5e433]:
                  - generic [ref=f5e434]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f5e435]:
                  - button "Sold out INCA 02 Styling Dust Wax 30g" [ref=f5e438] [cursor=pointer]:
                    - generic [ref=f5e439]: QUICK ADD
                    - generic [ref=f5e440]: ›
                  - generic [ref=f5e441]: IN STOCK
        - navigation "Pagination" [ref=f5e444]:
          - list [ref=f5e445]:
            - listitem [ref=f5e446]:
              - generic "Page 1" [ref=f5e447]: "1"
            - listitem [ref=f5e448]:
              - link "Page 2" [ref=f5e449] [cursor=pointer]:
                - /url: /collections/all?page=2
                - text: "2"
            - listitem [ref=f5e450]:
              - link "Page 3" [ref=f5e451] [cursor=pointer]:
                - /url: /collections/all?page=3
                - text: "3"
            - listitem [ref=f5e452]:
              - generic [ref=f5e453]: …
            - listitem [ref=f5e454]:
              - link "Page 5" [ref=f5e455] [cursor=pointer]:
                - /url: /collections/all?page=5
                - text: "5"
            - listitem [ref=f5e456]:
              - link "Next page" [ref=f5e457] [cursor=pointer]:
                - /url: /collections/all?page=2
  - link "To top" [ref=f5e460]:
    - /url: "#products"
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