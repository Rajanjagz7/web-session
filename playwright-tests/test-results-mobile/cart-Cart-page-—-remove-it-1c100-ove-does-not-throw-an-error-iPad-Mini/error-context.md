# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — remove items (RC-01..RC-02) >> RC-02 double-clicking remove does not throw an error
- Location: tests\cart.spec.ts:84:7

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
        - link [ref=f4e33] [cursor=pointer]:
          - /url: /account
  - main [ref=f4e37]:
    - navigation "breadcrumbs collection" [ref=f4e42]:
      - link "Home" [ref=f4e43]:
        - /url: /
      - link "All collections" [ref=f4e47]:
        - /url: /collections
      - generic [ref=f4e51]: Products
    - generic [ref=f4e55]:
      - img "Products" [ref=f4e57]
      - generic [ref=f4e59]:
        - heading "Products" [level=2] [ref=f4e60]
        - generic [ref=f4e61]: 52 PRODUCTS
    - generic [ref=f4e65]:
      - complementary "Filter:" [ref=f4e66]:
        - generic [ref=f4e67]:
          - group [ref=f4e69]:
            - generic "Filter and sort" [ref=f4e70] [cursor=pointer]
            - group:
              - generic "Price" [ref=f4e74] [cursor=pointer]
            - group:
              - generic "Product type" [ref=f4e78] [cursor=pointer]
            - group:
              - generic "Availability" [ref=f4e82] [cursor=pointer]
            - group:
              - generic "Brand" [ref=f4e86] [cursor=pointer]
            - option "Featured"
            - option "Most relevant"
            - option "Best selling"
            - option "Alphabetically, A-Z" [selected]
            - option "Alphabetically, Z-A"
            - option "Price, low to high"
            - option "Price, high to low"
            - option "Date, old to new"
            - option "Date, new to old"
          - status [ref=f4e90]:
            - heading "52 products" [level=2] [ref=f4e91]
      - generic [ref=f4e93]:
        - list [ref=f4e94]:
          - listitem [ref=f4e95]:
            - generic [ref=f4e97]:
              - generic [ref=f4e98]:
                - link [ref=f4e100]:
                  - /url: /products/andis-clipper-oil-118ml
                  - img "Andis Clipper Oil 118ml" [ref=f4e102]
                - generic:
                  - list:
                    - listitem [ref=f4e103]:
                      - generic "Add to wishlist" [ref=f4e105] [cursor=pointer]
              - generic [ref=f4e107]:
                - generic [ref=f4e108]: "Vendor:"
                - generic [ref=f4e109]: Andis
                - heading [level=6] [ref=f4e110]:
                  - link "Andis Clipper Oil 118ml" [ref=f4e111]:
                    - /url: /collections/all/products/andis-clipper-oil-118ml
                - generic [ref=f4e114]:
                  - generic [ref=f4e115]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e116]:
                  - button "Sold out Andis Clipper Oil 118ml" [ref=f4e119] [cursor=pointer]:
                    - generic [ref=f4e120]: QUICK ADD
                    - generic [ref=f4e121]: ›
                  - generic [ref=f4e122]: IN STOCK
          - listitem [ref=f4e124]:
            - generic [ref=f4e126]:
              - generic [ref=f4e127]:
                - link [ref=f4e129]:
                  - /url: /products/astra-blades-green-platinum
                  - img "Astra Green Platinum blade packaging" [ref=f4e131]
                - generic:
                  - list:
                    - listitem [ref=f4e132]:
                      - generic "Add to wishlist" [ref=f4e134] [cursor=pointer]
              - generic [ref=f4e136]:
                - generic [ref=f4e137]: "Vendor:"
                - generic [ref=f4e138]: Astra
                - heading [level=6] [ref=f4e139]:
                  - link "Astra Blades Green Platinum" [ref=f4e140]:
                    - /url: /collections/all/products/astra-blades-green-platinum
                - generic [ref=f4e143]:
                  - generic [ref=f4e144]: Regular price
                  - text: $14.50 AUD
                - generic [ref=f4e145]:
                  - button "Sold out Astra Blades Green Platinum" [ref=f4e148] [cursor=pointer]:
                    - generic [ref=f4e149]: QUICK ADD
                    - generic [ref=f4e150]: ›
                  - generic [ref=f4e151]: IN STOCK
          - listitem [ref=f4e153]:
            - generic [ref=f4e155]:
              - generic [ref=f4e156]:
                - link [ref=f4e158]:
                  - /url: /products/barbercon-acrylic-sterilizing-jar-1094ml
                  - generic [ref=f4e159]:
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e160]
                    - img "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e161]
                - generic:
                  - list:
                    - listitem [ref=f4e162]:
                      - generic "Add to wishlist" [ref=f4e164] [cursor=pointer]
              - generic [ref=f4e166]:
                - generic [ref=f4e167]: "Vendor:"
                - generic [ref=f4e168]: BarberCon
                - heading [level=6] [ref=f4e169]:
                  - link "BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e170]:
                    - /url: /collections/all/products/barbercon-acrylic-sterilizing-jar-1094ml
                - generic [ref=f4e173]:
                  - generic [ref=f4e174]: Regular price
                  - text: $27.23 AUD
                - generic [ref=f4e175]:
                  - button "Sold out BarberCon Acrylic Sterilizing Jar 1094ml" [ref=f4e178] [cursor=pointer]:
                    - generic [ref=f4e179]: QUICK ADD
                    - generic [ref=f4e180]: ›
                  - generic [ref=f4e181]: IN STOCK
          - listitem [ref=f4e183]:
            - generic [ref=f4e185]:
              - generic [ref=f4e186]:
                - link [ref=f4e188]:
                  - /url: /products/barbercon-neck-strips-white
                  - img "BarberCon Neck Strips - White" [ref=f4e190]
                - generic:
                  - list:
                    - listitem [ref=f4e191]:
                      - generic "Add to wishlist" [ref=f4e193] [cursor=pointer]
              - generic [ref=f4e195]:
                - generic [ref=f4e196]: "Vendor:"
                - generic [ref=f4e197]: BarberCon
                - heading [level=6] [ref=f4e198]:
                  - link "BarberCon Neck Strips - White" [ref=f4e199]:
                    - /url: /collections/all/products/barbercon-neck-strips-white
                - generic [ref=f4e202]:
                  - generic [ref=f4e203]: Regular price
                  - text: $6.32 AUD
                - generic [ref=f4e204]:
                  - button "Sold out BarberCon Neck Strips - White" [ref=f4e207] [cursor=pointer]:
                    - generic [ref=f4e208]: QUICK ADD
                    - generic [ref=f4e209]: ›
                  - generic [ref=f4e210]: IN STOCK
          - listitem [ref=f4e212]:
            - generic [ref=f4e214]:
              - generic [ref=f4e215]:
                - link [ref=f4e217]:
                  - /url: /products/barbercon-wax-pot-black
                  - img "BarberCon Wax Pot Black" [ref=f4e219]
                - generic:
                  - list:
                    - listitem [ref=f4e220]:
                      - generic "Add to wishlist" [ref=f4e222] [cursor=pointer]
              - generic [ref=f4e224]:
                - generic [ref=f4e225]: "Vendor:"
                - generic [ref=f4e226]: BarberCon
                - heading [level=6] [ref=f4e227]:
                  - link "BarberCon Wax Pot Black" [ref=f4e228]:
                    - /url: /collections/all/products/barbercon-wax-pot-black
                - generic [ref=f4e231]:
                  - generic [ref=f4e232]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f4e233]:
                  - button "Sold out BarberCon Wax Pot Black" [ref=f4e236] [cursor=pointer]:
                    - generic [ref=f4e237]: QUICK ADD
                    - generic [ref=f4e238]: ›
                  - generic [ref=f4e239]: IN STOCK
          - listitem [ref=f4e241]:
            - generic [ref=f4e243]:
              - generic [ref=f4e244]:
                - link [ref=f4e246]:
                  - /url: /products/barbercon-wax-pot-white
                  - img "BarberCon Wax Pot White" [ref=f4e248]
                - generic:
                  - list:
                    - listitem [ref=f4e249]:
                      - generic "Add to wishlist" [ref=f4e251] [cursor=pointer]
              - generic [ref=f4e253]:
                - generic [ref=f4e254]: "Vendor:"
                - generic [ref=f4e255]: BarberCon
                - heading [level=6] [ref=f4e256]:
                  - link "BarberCon Wax Pot White" [ref=f4e257]:
                    - /url: /collections/all/products/barbercon-wax-pot-white
                - generic [ref=f4e260]:
                  - generic [ref=f4e261]: Regular price
                  - text: $72.68 AUD
                - generic [ref=f4e262]:
                  - button "Sold out BarberCon Wax Pot White" [ref=f4e265] [cursor=pointer]:
                    - generic [ref=f4e266]: QUICK ADD
                    - generic [ref=f4e267]: ›
                  - generic [ref=f4e268]: IN STOCK
          - listitem [ref=f4e270]:
            - generic [ref=f4e272]:
              - generic [ref=f4e273]:
                - link [ref=f4e275]:
                  - /url: /products/carbon-comb-abs-70739
                  - img "Carbon Comb ABS-70739" [ref=f4e277]
                - generic:
                  - list:
                    - listitem [ref=f4e278]:
                      - generic "Add to wishlist" [ref=f4e280] [cursor=pointer]
              - generic [ref=f4e282]:
                - generic [ref=f4e283]: "Vendor:"
                - generic [ref=f4e284]: H2B / Generic
                - heading [level=6] [ref=f4e285]:
                  - link "Carbon Comb ABS-70739" [ref=f4e286]:
                    - /url: /collections/all/products/carbon-comb-abs-70739
                - generic [ref=f4e289]:
                  - generic [ref=f4e290]: Regular price
                  - text: $7.23 AUD
                - generic [ref=f4e291]:
                  - button "Sold out Carbon Comb ABS-70739" [ref=f4e294] [cursor=pointer]:
                    - generic [ref=f4e295]: QUICK ADD
                    - generic [ref=f4e296]: ›
                  - generic [ref=f4e297]: IN STOCK
          - listitem [ref=f4e299]:
            - generic [ref=f4e301]:
              - generic [ref=f4e302]:
                - link [ref=f4e304]:
                  - /url: /products/carbon-small-cutting-comb-cfc-08139
                  - img "Carbon Small Cutting Comb CFC-08139" [ref=f4e306]
                - generic:
                  - list:
                    - listitem [ref=f4e307]:
                      - generic "Add to wishlist" [ref=f4e309] [cursor=pointer]
              - generic [ref=f4e311]:
                - generic [ref=f4e312]: "Vendor:"
                - generic [ref=f4e313]: H2B / Generic
                - heading [level=6] [ref=f4e314]:
                  - link "Carbon Small Cutting Comb CFC-08139" [ref=f4e315]:
                    - /url: /collections/all/products/carbon-small-cutting-comb-cfc-08139
                - generic [ref=f4e318]:
                  - generic [ref=f4e319]: Regular price
                  - text: $4.50 AUD
                - generic [ref=f4e320]:
                  - button "Sold out Carbon Small Cutting Comb CFC-08139" [ref=f4e323] [cursor=pointer]:
                    - generic [ref=f4e324]: QUICK ADD
                    - generic [ref=f4e325]: ›
                  - generic [ref=f4e326]: IN STOCK
          - listitem [ref=f4e328]:
            - generic [ref=f4e330]:
              - generic [ref=f4e331]:
                - link [ref=f4e333]:
                  - /url: /products/clippercide-spray-425g
                  - img "Clippercide Spray 425g" [ref=f4e335]
                - generic:
                  - list:
                    - listitem [ref=f4e336]:
                      - generic "Add to wishlist" [ref=f4e338] [cursor=pointer]
              - generic [ref=f4e340]:
                - generic [ref=f4e341]: "Vendor:"
                - generic [ref=f4e342]: Clippercide
                - heading [level=6] [ref=f4e343]:
                  - link "Clippercide Spray 425g" [ref=f4e344]:
                    - /url: /collections/all/products/clippercide-spray-425g
                - generic [ref=f4e347]:
                  - generic [ref=f4e348]: Regular price
                  - text: $18.14 AUD
                - generic [ref=f4e349]:
                  - button "Sold out Clippercide Spray 425g" [ref=f4e352] [cursor=pointer]:
                    - generic [ref=f4e353]: QUICK ADD
                    - generic [ref=f4e354]: ›
                  - generic [ref=f4e355]: IN STOCK
          - listitem [ref=f4e357]:
            - generic [ref=f4e359]:
              - generic [ref=f4e360]:
                - link [ref=f4e362]:
                  - /url: /products/coffee-stirrers-1000pcs
                  - img "Coffee Stirrers 1000pcs" [ref=f4e364]
                - generic:
                  - list:
                    - listitem [ref=f4e365]:
                      - generic "Add to wishlist" [ref=f4e367] [cursor=pointer]
              - generic [ref=f4e369]:
                - generic [ref=f4e370]: "Vendor:"
                - generic [ref=f4e371]: Generic
                - heading [level=6] [ref=f4e372]:
                  - link "Coffee Stirrers 1000pcs" [ref=f4e373]:
                    - /url: /collections/all/products/coffee-stirrers-1000pcs
                - generic [ref=f4e376]:
                  - generic [ref=f4e377]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e378]:
                  - button "Sold out Coffee Stirrers 1000pcs" [ref=f4e381] [cursor=pointer]:
                    - generic [ref=f4e382]: QUICK ADD
                    - generic [ref=f4e383]: ›
                  - generic [ref=f4e384]: IN STOCK
          - listitem [ref=f4e386]:
            - generic [ref=f4e388]:
              - generic [ref=f4e389]:
                - link [ref=f4e391]:
                  - /url: /products/cosma-liquid-styptic-25ml
                  - img "Cosma Liquid Styptic 25ml" [ref=f4e393]
                - generic:
                  - list:
                    - listitem [ref=f4e394]:
                      - generic "Add to wishlist" [ref=f4e396] [cursor=pointer]
              - generic [ref=f4e398]:
                - generic [ref=f4e399]: "Vendor:"
                - generic [ref=f4e400]: Cosma
                - heading [level=6] [ref=f4e401]:
                  - link "Cosma Liquid Styptic 25ml" [ref=f4e402]:
                    - /url: /collections/all/products/cosma-liquid-styptic-25ml
                - generic [ref=f4e405]:
                  - generic [ref=f4e406]: Regular price
                  - text: $10.86 AUD
                - generic [ref=f4e407]:
                  - button "Sold out Cosma Liquid Styptic 25ml" [ref=f4e410] [cursor=pointer]:
                    - generic [ref=f4e411]: QUICK ADD
                    - generic [ref=f4e412]: ›
                  - generic [ref=f4e413]: IN STOCK
          - listitem [ref=f4e415]:
            - generic [ref=f4e417]:
              - generic [ref=f4e418]:
                - link [ref=f4e420]:
                  - /url: /products/inca-02-styling-dust-wax-30g
                  - img "INCA 02 Styling Dust Wax 30g" [ref=f4e422]
                - generic:
                  - list:
                    - listitem [ref=f4e423]:
                      - generic "Add to wishlist" [ref=f4e425] [cursor=pointer]
              - generic [ref=f4e427]:
                - generic [ref=f4e428]: "Vendor:"
                - generic [ref=f4e429]: ProRapid
                - heading [level=6] [ref=f4e430]:
                  - link "INCA 02 Styling Dust Wax 30g" [ref=f4e431]:
                    - /url: /collections/all/products/inca-02-styling-dust-wax-30g
                - generic [ref=f4e434]:
                  - generic [ref=f4e435]: Regular price
                  - text: $9.05 AUD
                - generic [ref=f4e436]:
                  - button "Sold out INCA 02 Styling Dust Wax 30g" [ref=f4e439] [cursor=pointer]:
                    - generic [ref=f4e440]: QUICK ADD
                    - generic [ref=f4e441]: ›
                  - generic [ref=f4e442]: IN STOCK
        - navigation "Pagination" [ref=f4e445]:
          - list [ref=f4e446]:
            - listitem [ref=f4e447]:
              - generic "Page 1" [ref=f4e448]: "1"
            - listitem [ref=f4e449]:
              - link "Page 2" [ref=f4e450] [cursor=pointer]:
                - /url: /collections/all?page=2
                - text: "2"
            - listitem [ref=f4e451]:
              - link "Page 3" [ref=f4e452] [cursor=pointer]:
                - /url: /collections/all?page=3
                - text: "3"
            - listitem [ref=f4e453]:
              - generic [ref=f4e454]: …
            - listitem [ref=f4e455]:
              - link "Page 5" [ref=f4e456] [cursor=pointer]:
                - /url: /collections/all?page=5
                - text: "5"
            - listitem [ref=f4e457]:
              - link "Next page" [ref=f4e458] [cursor=pointer]:
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