# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-cart.spec.ts >> Product page — add to cart (PA-01..PA-08) >> PA-01 quantity zero blocks add to cart
- Location: tests\product-cart.spec.ts:8:7

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
        - link [ref=f4e32] [cursor=pointer]:
          - /url: /account
  - main [ref=f4e36]:
    - navigation "breadcrumbs collection" [ref=f4e41]:
      - link "Home" [ref=f4e42]:
        - /url: /
      - link "All collections" [ref=f4e46]:
        - /url: /collections
      - generic [ref=f4e50]: Products
    - generic [ref=f4e54]:
      - img "Products" [ref=f4e56]
      - generic [ref=f4e58]:
        - heading "Products" [level=2] [ref=f4e59]
        - generic [ref=f4e60]: 52 PRODUCTS
    - generic [ref=f4e64]:
      - complementary "Filter:" [ref=f4e65]:
        - generic [ref=f4e66]:
          - group [ref=f4e68]:
            - generic "Filter and sort" [ref=f4e69] [cursor=pointer]
            - group:
              - button "Price" [ref=f4e73] [cursor=pointer]
            - group:
              - button "Product type" [ref=f4e77] [cursor=pointer]
            - group:
              - button "Availability" [ref=f4e81] [cursor=pointer]
            - group:
              - button "Brand" [ref=f4e85] [cursor=pointer]
            - option "Featured"
            - option "Most relevant"
            - option "Best selling"
            - option "Alphabetically, A-Z" [selected]
            - option "Alphabetically, Z-A"
            - option "Price, low to high"
            - option "Price, high to low"
            - option "Date, old to new"
            - option "Date, new to old"
          - status [ref=f4e89]:
            - heading "52 products" [level=2] [ref=f4e90]
      - generic [ref=f4e92]:
        - list [ref=f4e93]:
          - listitem [ref=f4e94]:
            - generic [ref=f4e96]:
              - generic [ref=f4e97]:
                - link [ref=f4e99]:
                  - /url: /products/andis-clipper-oil-118ml
                  - img "Andis Clipper Oil 118ml" [ref=f4e101]
                - generic:
                  - list:
                    - listitem [ref=f4e102]:
                      - generic "Add to wishlist" [ref=f4e104] [cursor=pointer]
              - generic [ref=f4e106]:
                - generic [ref=f4e107]: "Vendor:"
                - generic [ref=f4e108]: Andis
                - heading [level=6] [ref=f4e109]:
                  - link "Andis Clipper Oil 118ml" [ref=f4e110]:
                    - /url: /collections/all/products/andis-clipper-oil-118ml
                - generic [ref=f4e113]:
                  - generic [ref=f4e114]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e115]:
                  - button "Sold out Andis Clipper Oil 118ml" [ref=f4e118] [cursor=pointer]:
                    - generic [ref=f4e119]: QUICK ADD
                    - generic [ref=f4e120]: ›
                  - generic [ref=f4e121]: IN STOCK
          - listitem [ref=f4e123]:
            - generic [ref=f4e125]:
              - generic [ref=f4e126]:
                - link [ref=f4e128]:
                  - /url: /products/astra-blades-green-platinum
                  - img "Astra Green Platinum blade packaging" [ref=f4e130]
                - generic:
                  - list:
                    - listitem [ref=f4e131]:
                      - generic "Add to wishlist" [ref=f4e133] [cursor=pointer]
              - generic [ref=f4e135]:
                - generic [ref=f4e136]: "Vendor:"
                - generic [ref=f4e137]: Astra
                - heading [level=6] [ref=f4e138]:
                  - link "Astra Blades Green Platinum" [ref=f4e139]:
                    - /url: /collections/all/products/astra-blades-green-platinum
                - generic [ref=f4e142]:
                  - generic [ref=f4e143]: Regular price
                  - text: $14.50 AUD
                - generic [ref=f4e144]:
                  - button "Sold out Astra Blades Green Platinum" [ref=f4e147] [cursor=pointer]:
                    - generic [ref=f4e148]: QUICK ADD
                    - generic [ref=f4e149]: ›
                  - generic [ref=f4e150]: IN STOCK
          - listitem [ref=f4e152]:
            - generic [ref=f4e154]:
              - generic [ref=f4e155]:
                - link [ref=f4e157]:
                  - /url: /products/barbercon-acrylic-sterilizing-jar-1094ml
                  - generic [ref=f4e158]:
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e159]
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e160]
                - generic:
                  - list:
                    - listitem [ref=f4e161]:
                      - generic "Add to wishlist" [ref=f4e163] [cursor=pointer]
              - generic [ref=f4e165]:
                - generic [ref=f4e166]: "Vendor:"
                - generic [ref=f4e167]: BarberCon
                - heading [level=6] [ref=f4e168]:
                  - link "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e169]:
                    - /url: /collections/all/products/barbercon-acrylic-sterilizing-jar-1094ml
                - generic [ref=f4e172]:
                  - generic [ref=f4e173]: Regular price
                  - text: $27.23 AUD
                - generic [ref=f4e174]:
                  - button "Sold out BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e177] [cursor=pointer]:
                    - generic [ref=f4e178]: QUICK ADD
                    - generic [ref=f4e179]: ›
                  - generic [ref=f4e180]: IN STOCK
          - listitem [ref=f4e182]:
            - generic [ref=f4e184]:
              - generic [ref=f4e185]:
                - link [ref=f4e187]:
                  - /url: /products/barbercon-neck-strips-white
                  - img "BarberCon Neck Strips - White" [ref=f4e189]
                - generic:
                  - list:
                    - listitem [ref=f4e190]:
                      - generic "Add to wishlist" [ref=f4e192] [cursor=pointer]
              - generic [ref=f4e194]:
                - generic [ref=f4e195]: "Vendor:"
                - generic [ref=f4e196]: BarberCon
                - heading [level=6] [ref=f4e197]:
                  - link "BarberCon Neck Strips - White" [ref=f4e198]:
                    - /url: /collections/all/products/barbercon-neck-strips-white
                - generic [ref=f4e201]:
                  - generic [ref=f4e202]: Regular price
                  - text: $6.32 AUD
                - generic [ref=f4e203]:
                  - button "Sold out BarberCon Neck Strips - White" [ref=f4e206] [cursor=pointer]:
                    - generic [ref=f4e207]: QUICK ADD
                    - generic [ref=f4e208]: ›
                  - generic [ref=f4e209]: IN STOCK
          - listitem [ref=f4e211]:
            - generic [ref=f4e213]:
              - generic [ref=f4e214]:
                - link [ref=f4e216]:
                  - /url: /products/barbercon-wax-pot-black
                  - img "BarberCon Wax Pot Black" [ref=f4e218]
                - generic:
                  - list:
                    - listitem [ref=f4e219]:
                      - generic "Add to wishlist" [ref=f4e221] [cursor=pointer]
              - generic [ref=f4e223]:
                - generic [ref=f4e224]: "Vendor:"
                - generic [ref=f4e225]: BarberCon
                - heading [level=6] [ref=f4e226]:
                  - link "BarberCon Wax Pot Black" [ref=f4e227]:
                    - /url: /collections/all/products/barbercon-wax-pot-black
                - generic [ref=f4e230]:
                  - generic [ref=f4e231]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f4e232]:
                  - button "Sold out BarberCon Wax Pot Black" [ref=f4e235] [cursor=pointer]:
                    - generic [ref=f4e236]: QUICK ADD
                    - generic [ref=f4e237]: ›
                  - generic [ref=f4e238]: IN STOCK
          - listitem [ref=f4e240]:
            - generic [ref=f4e242]:
              - generic [ref=f4e243]:
                - link [ref=f4e245]:
                  - /url: /products/barbercon-wax-pot-white
                  - img "BarberCon Wax Pot White" [ref=f4e247]
                - generic:
                  - list:
                    - listitem [ref=f4e248]:
                      - generic "Add to wishlist" [ref=f4e250] [cursor=pointer]
              - generic [ref=f4e252]:
                - generic [ref=f4e253]: "Vendor:"
                - generic [ref=f4e254]: BarberCon
                - heading [level=6] [ref=f4e255]:
                  - link "BarberCon Wax Pot White" [ref=f4e256]:
                    - /url: /collections/all/products/barbercon-wax-pot-white
                - generic [ref=f4e259]:
                  - generic [ref=f4e260]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f4e261]:
                  - button "Sold out BarberCon Wax Pot White" [ref=f4e264] [cursor=pointer]:
                    - generic [ref=f4e265]: QUICK ADD
                    - generic [ref=f4e266]: ›
                  - generic [ref=f4e267]: IN STOCK
          - listitem [ref=f4e269]:
            - generic [ref=f4e271]:
              - generic [ref=f4e272]:
                - link [ref=f4e274]:
                  - /url: /products/carbon-comb-abs-70739
                  - img "Carbon Comb ABS-70739" [ref=f4e276]
                - generic:
                  - list:
                    - listitem [ref=f4e277]:
                      - generic "Add to wishlist" [ref=f4e279] [cursor=pointer]
              - generic [ref=f4e281]:
                - generic [ref=f4e282]: "Vendor:"
                - generic [ref=f4e283]: H2B / Generic
                - heading [level=6] [ref=f4e284]:
                  - link "Carbon Comb ABS-70739" [ref=f4e285]:
                    - /url: /collections/all/products/carbon-comb-abs-70739
                - generic [ref=f4e288]:
                  - generic [ref=f4e289]: Regular price
                  - text: $7.23 AUD
                - generic [ref=f4e290]:
                  - button "Sold out Carbon Comb ABS-70739" [ref=f4e293] [cursor=pointer]:
                    - generic [ref=f4e294]: QUICK ADD
                    - generic [ref=f4e295]: ›
                  - generic [ref=f4e296]: IN STOCK
          - listitem [ref=f4e298]:
            - generic [ref=f4e300]:
              - generic [ref=f4e301]:
                - link [ref=f4e303]:
                  - /url: /products/carbon-small-cutting-comb-cfc-08139
                  - img "Carbon Small Cutting Comb CFC-08139" [ref=f4e305]
                - generic:
                  - list:
                    - listitem [ref=f4e306]:
                      - generic "Add to wishlist" [ref=f4e308] [cursor=pointer]
              - generic [ref=f4e310]:
                - generic [ref=f4e311]: "Vendor:"
                - generic [ref=f4e312]: H2B / Generic
                - heading [level=6] [ref=f4e313]:
                  - link "Carbon Small Cutting Comb CFC-08139" [ref=f4e314]:
                    - /url: /collections/all/products/carbon-small-cutting-comb-cfc-08139
                - generic [ref=f4e317]:
                  - generic [ref=f4e318]: Regular price
                  - text: $4.50 AUD
                - generic [ref=f4e319]:
                  - button "Sold out Carbon Small Cutting Comb CFC-08139" [ref=f4e322] [cursor=pointer]:
                    - generic [ref=f4e323]: QUICK ADD
                    - generic [ref=f4e324]: ›
                  - generic [ref=f4e325]: IN STOCK
          - listitem [ref=f4e327]:
            - generic [ref=f4e329]:
              - generic [ref=f4e330]:
                - link [ref=f4e332]:
                  - /url: /products/clippercide-spray-425g
                  - img "Clippercide Spray 425g" [ref=f4e334]
                - generic:
                  - list:
                    - listitem [ref=f4e335]:
                      - generic "Add to wishlist" [ref=f4e337] [cursor=pointer]
              - generic [ref=f4e339]:
                - generic [ref=f4e340]: "Vendor:"
                - generic [ref=f4e341]: Clippercide
                - heading [level=6] [ref=f4e342]:
                  - link "Clippercide Spray 425g" [ref=f4e343]:
                    - /url: /collections/all/products/clippercide-spray-425g
                - generic [ref=f4e346]:
                  - generic [ref=f4e347]: Regular price
                  - text: $18.14 AUD
                - generic [ref=f4e348]:
                  - button "Sold out Clippercide Spray 425g" [ref=f4e351] [cursor=pointer]:
                    - generic [ref=f4e352]: QUICK ADD
                    - generic [ref=f4e353]: ›
                  - generic [ref=f4e354]: IN STOCK
          - listitem [ref=f4e356]:
            - generic [ref=f4e358]:
              - generic [ref=f4e359]:
                - link [ref=f4e361]:
                  - /url: /products/coffee-stirrers-1000pcs
                  - img "Coffee Stirrers 1000pcs" [ref=f4e363]
                - generic:
                  - list:
                    - listitem [ref=f4e364]:
                      - generic "Add to wishlist" [ref=f4e366] [cursor=pointer]
              - generic [ref=f4e368]:
                - generic [ref=f4e369]: "Vendor:"
                - generic [ref=f4e370]: Generic
                - heading [level=6] [ref=f4e371]:
                  - link "Coffee Stirrers 1000pcs" [ref=f4e372]:
                    - /url: /collections/all/products/coffee-stirrers-1000pcs
                - generic [ref=f4e375]:
                  - generic [ref=f4e376]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e377]:
                  - button "Sold out Coffee Stirrers 1000pcs" [ref=f4e380] [cursor=pointer]:
                    - generic [ref=f4e381]: QUICK ADD
                    - generic [ref=f4e382]: ›
                  - generic [ref=f4e383]: IN STOCK
          - listitem [ref=f4e385]:
            - generic [ref=f4e387]:
              - generic [ref=f4e388]:
                - link [ref=f4e390]:
                  - /url: /products/cosma-liquid-styptic-25ml
                  - img "Cosma Liquid Styptic 25ml" [ref=f4e392]
                - generic:
                  - list:
                    - listitem [ref=f4e393]:
                      - generic "Add to wishlist" [ref=f4e395] [cursor=pointer]
              - generic [ref=f4e397]:
                - generic [ref=f4e398]: "Vendor:"
                - generic [ref=f4e399]: Cosma
                - heading [level=6] [ref=f4e400]:
                  - link "Cosma Liquid Styptic 25ml" [ref=f4e401]:
                    - /url: /collections/all/products/cosma-liquid-styptic-25ml
                - generic [ref=f4e404]:
                  - generic [ref=f4e405]: Regular price
                  - text: $10.86 AUD
                - generic [ref=f4e406]:
                  - button "Sold out Cosma Liquid Styptic 25ml" [ref=f4e409] [cursor=pointer]:
                    - generic [ref=f4e410]: QUICK ADD
                    - generic [ref=f4e411]: ›
                  - generic [ref=f4e412]: IN STOCK
          - listitem [ref=f4e414]:
            - generic [ref=f4e416]:
              - generic [ref=f4e417]:
                - link [ref=f4e419]:
                  - /url: /products/inca-02-styling-dust-wax-30g
                  - img "INCA 02 Styling Dust Wax 30g" [ref=f4e421]
                - generic:
                  - list:
                    - listitem [ref=f4e422]:
                      - generic "Add to wishlist" [ref=f4e424] [cursor=pointer]
              - generic [ref=f4e426]:
                - generic [ref=f4e427]: "Vendor:"
                - generic [ref=f4e428]: ProRapid
                - heading [level=6] [ref=f4e429]:
                  - link "INCA 02 Styling Dust Wax 30g" [ref=f4e430]:
                    - /url: /collections/all/products/inca-02-styling-dust-wax-30g
                - generic [ref=f4e433]:
                  - generic [ref=f4e434]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e435]:
                  - button "Sold out INCA 02 Styling Dust Wax 30g" [ref=f4e438] [cursor=pointer]:
                    - generic [ref=f4e439]: QUICK ADD
                    - generic [ref=f4e440]: ›
                  - generic [ref=f4e441]: IN STOCK
        - navigation "Pagination" [ref=f4e444]:
          - list [ref=f4e445]:
            - listitem [ref=f4e446]:
              - generic "Page 1" [ref=f4e447]: "1"
            - listitem [ref=f4e448]:
              - link "Page 2" [ref=f4e449] [cursor=pointer]:
                - /url: /collections/all?page=2
                - text: "2"
            - listitem [ref=f4e450]:
              - link "Page 3" [ref=f4e451] [cursor=pointer]:
                - /url: /collections/all?page=3
                - text: "3"
            - listitem [ref=f4e452]:
              - generic [ref=f4e453]: …
            - listitem [ref=f4e454]:
              - link "Page 5" [ref=f4e455] [cursor=pointer]:
                - /url: /collections/all?page=5
                - text: "5"
            - listitem [ref=f4e456]:
              - link "Next page" [ref=f4e457] [cursor=pointer]:
                - /url: /collections/all?page=2
  - link "To top" [ref=f4e460]:
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