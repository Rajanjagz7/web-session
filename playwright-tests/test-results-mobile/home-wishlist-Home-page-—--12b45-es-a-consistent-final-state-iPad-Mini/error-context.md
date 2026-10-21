# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: home-wishlist.spec.ts >> Home page — wishlist (WL-01..WL-05) >> WL-05 spam-clicking the toggle leaves a consistent final state
- Location: tests\home-wishlist.spec.ts:35:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('[class*="wishlist"], [aria-label*="wishlist" i], button[data-wishlist]').first()
    - locator resolved to <a href="/pages/wishlist" class="header__icon header__icon--wishlist link small-hidedt__wishlist-show">…</a>
  - attempting click action
    - waiting for element to be visible, enabled and stable

```

# Page snapshot

```yaml
- generic [active] [ref=f2e1]:
  - banner [ref=f2e4]:
    - generic [ref=f2e7]:
      - group [ref=f2e9]:
        - button "Menu" [ref=f2e10] [cursor=pointer]
      - heading [level=1] [ref=f2e13]:
        - link [ref=f2e14] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f2e15]
      - generic [ref=f2e16]:
        - generic [ref=f2e17] [cursor=pointer]
        - link [ref=f2e21] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f2e24] [cursor=pointer]
        - link [ref=f2e31] [cursor=pointer]:
          - /url: /account
  - main [ref=f2e35]:
    - group "1 / 1" [ref=f2e43]:
      - generic [ref=f2e46]:
        - heading "PROFESSIONAL GROOMING" [level=6] [ref=f2e47]
        - heading "LEVEL UP YOUR GROOMING GAME" [level=2] [ref=f2e48]
        - generic [ref=f2e49]: Premium pomades, beard care and shave essentials — built for the modern man.
        - generic [ref=f2e50]:
          - link "Shop Styling" [ref=f2e51] [cursor=pointer]:
            - /url: /collections
          - link "Explore Bundles" [ref=f2e53] [cursor=pointer]:
            - /url: /collections/bundles-kits
    - generic [ref=f2e59]:
      - heading "WHO WE ARE" [level=6] [ref=f2e61]
      - heading [level=3] [ref=f2e64]:
        - text: Built for barbers,creators, and men who care about precision. ZeroGap brings
        - strong [ref=f2e65]: professional-grade
        - text: grooming essentials in one sharp online experience.
    - generic [ref=f2e71]:
      - generic [ref=f2e72]:
        - listitem [ref=f2e73]:
          - heading "UNLOCK THE SHARP" [level=2] [ref=f2e74]
        - listitem [ref=f2e75]:
          - heading "DISCOVER THE ZERO GAP" [level=2] [ref=f2e76]
      - generic [ref=f2e77]:
        - listitem [ref=f2e78]:
          - heading "UNLOCK THE SHARP" [level=2] [ref=f2e79]
        - listitem [ref=f2e80]:
          - heading "DISCOVER THE ZERO GAP" [level=2] [ref=f2e81]
    - generic [ref=f2e85]:
      - generic [ref=f2e86]:
        - heading "OUR CATEGORIES" [level=6] [ref=f2e87]
        - heading "KEY GROOMING ESSENTIALS" [level=2] [ref=f2e88]
      - list "Slider" [ref=f2e92]:
        - group "1 / 2" [ref=f2e93]:
          - generic [ref=f2e95]:
            - generic [ref=f2e96]:
              - link [ref=f2e98]:
                - /url: /products/uppercut-matte-pomade
                - img "Uppercut Deluxe Matte Pomade" [ref=f2e100]
              - generic:
                - list:
                  - listitem [ref=f2e101]:
                    - generic "Add to wishlist" [ref=f2e103] [cursor=pointer]
            - generic [ref=f2e105]:
              - generic [ref=f2e106]: "Vendor:"
              - generic [ref=f2e107]: Uppercut Deluxe
              - heading [level=6] [ref=f2e108]:
                - link "Uppercut Deluxe Matte Pomade" [ref=f2e109]:
                  - /url: /products/uppercut-matte-pomade
              - generic [ref=f2e112]:
                - generic [ref=f2e113]: Regular price
                - text: $11.82 AUD
              - generic [ref=f2e114]:
                - button "Sold out Uppercut Deluxe Matte Pomade" [ref=f2e117] [cursor=pointer]:
                  - generic [ref=f2e118]: QUICK ADD
                  - generic [ref=f2e119]: ›
                - generic [ref=f2e120]: IN STOCK
        - group "2 / 2" [ref=f2e122]:
          - generic [ref=f2e124]:
            - generic [ref=f2e125]:
              - link [ref=f2e127]:
                - /url: /products/uppercut-deluxe-pomade
                - img "Uppercut Deluxe Pomade" [ref=f2e129]
              - generic:
                - list:
                  - listitem [ref=f2e130]:
                    - generic "Add to wishlist" [ref=f2e132] [cursor=pointer]
            - generic [ref=f2e134]:
              - generic [ref=f2e135]: "Vendor:"
              - generic [ref=f2e136]: Uppercut Deluxe
              - heading [level=6] [ref=f2e137]:
                - link "Uppercut Deluxe Pomade" [ref=f2e138]:
                  - /url: /products/uppercut-deluxe-pomade
              - generic [ref=f2e141]:
                - generic [ref=f2e142]: Regular price
                - text: $11.82 AUD
              - generic [ref=f2e143]:
                - button "Sold out Uppercut Deluxe Pomade" [ref=f2e146] [cursor=pointer]:
                  - generic [ref=f2e147]: QUICK ADD
                  - generic [ref=f2e148]: ›
                - generic [ref=f2e149]: IN STOCK
    - generic [ref=f2e154]:
      - generic [ref=f2e155]:
        - heading "FEATURED" [level=6] [ref=f2e156]
        - heading "BEST SELLERS" [level=2] [ref=f2e157]
      - list "Slider" [ref=f2e161]:
        - group "1 / 8" [ref=f2e162]:
          - generic [ref=f2e164]:
            - generic [ref=f2e165]:
              - link [ref=f2e167]:
                - /url: /products/prorapid-tattoo-series-inca-09-after-shave-perfumed-cologne-400-ml
                - img "ProRapid Tattoo Series Inca 09 After Shave Perfumed Cologne 400 ml" [ref=f2e169]
              - generic:
                - list:
                  - listitem [ref=f2e170]:
                    - generic "Add to wishlist" [ref=f2e172] [cursor=pointer]
            - generic [ref=f2e174]:
              - heading [level=6] [ref=f2e175]:
                - link "ProRapid Tattoo Series Inca 09 After Shave Perfumed Cologne 400 ml" [ref=f2e176]:
                  - /url: /products/prorapid-tattoo-series-inca-09-after-shave-perfumed-cologne-400-ml
              - generic [ref=f2e179]:
                - generic [ref=f2e180]: Regular price
                - text: $6.32 AUD
              - generic [ref=f2e181]:
                - button "Sold out ProRapid Tattoo Series Inca 09 After Shave Perfumed Cologne 400 ml" [ref=f2e184] [cursor=pointer]:
                  - generic [ref=f2e185]: QUICK ADD
                  - generic [ref=f2e186]: ›
                - generic [ref=f2e187]: IN STOCK
        - group "2 / 8" [ref=f2e189]:
          - generic [ref=f2e191]:
            - generic [ref=f2e192]:
              - link [ref=f2e194]:
                - /url: /products/prorapid-tattoo-series-inca-02-after-shave-perfumed-cologne-400-ml
                - img "ProRapid Tattoo Series Inca 02 After Shave Perfumed Cologne 400 ml" [ref=f2e196]
              - generic:
                - list:
                  - listitem [ref=f2e197]:
                    - generic "Add to wishlist" [ref=f2e199] [cursor=pointer]
            - generic [ref=f2e201]:
              - heading [level=6] [ref=f2e202]:
                - link "ProRapid Tattoo Series Inca 02 After Shave Perfumed Cologne 400 ml" [ref=f2e203]:
                  - /url: /products/prorapid-tattoo-series-inca-02-after-shave-perfumed-cologne-400-ml
              - generic [ref=f2e206]:
                - generic [ref=f2e207]: Regular price
                - text: $6.32 AUD
              - generic [ref=f2e208]:
                - button "Sold out ProRapid Tattoo Series Inca 02 After Shave Perfumed Cologne 400 ml" [ref=f2e211] [cursor=pointer]:
                  - generic [ref=f2e212]: QUICK ADD
                  - generic [ref=f2e213]: ›
                - generic [ref=f2e214]: IN STOCK
        - group "3 / 8" [ref=f2e216]:
          - generic [ref=f2e218]:
            - generic [ref=f2e219]:
              - link [ref=f2e221]:
                - /url: /products/prorapid-tattoo-series-inca-07-after-shave-perfumed-cologne-400-ml
                - img "ProRapid Tattoo Series Inca 07 After Shave Perfumed Cologne 400 ml" [ref=f2e223]
              - generic:
                - list:
                  - listitem [ref=f2e224]:
                    - generic "Add to wishlist" [ref=f2e226] [cursor=pointer]
            - generic [ref=f2e228]:
              - heading [level=6] [ref=f2e229]:
                - link "ProRapid Tattoo Series Inca 07 After Shave Perfumed Cologne 400 ml" [ref=f2e230]:
                  - /url: /products/prorapid-tattoo-series-inca-07-after-shave-perfumed-cologne-400-ml
              - generic [ref=f2e233]:
                - generic [ref=f2e234]: Regular price
                - text: $6.32 AUD
              - generic [ref=f2e235]:
                - button "Sold out ProRapid Tattoo Series Inca 07 After Shave Perfumed Cologne 400 ml" [ref=f2e238] [cursor=pointer]:
                  - generic [ref=f2e239]: QUICK ADD
                  - generic [ref=f2e240]: ›
                - generic [ref=f2e241]: IN STOCK
        - group "4 / 8" [ref=f2e243]:
          - generic [ref=f2e245]:
            - generic [ref=f2e246]:
              - link [ref=f2e248]:
                - /url: /products/prorapid-tattoo-series-inca-08-after-shave-perfumed-cologne-400-ml
                - img "ProRapid Tattoo Series Inca 08 After Shave Perfumed Cologne 400 ml" [ref=f2e250]
              - generic:
                - list:
                  - listitem [ref=f2e251]:
                    - generic "Add to wishlist" [ref=f2e253] [cursor=pointer]
            - generic [ref=f2e255]:
              - heading [level=6] [ref=f2e256]:
                - link "ProRapid Tattoo Series Inca 08 After Shave Perfumed Cologne 400 ml" [ref=f2e257]:
                  - /url: /products/prorapid-tattoo-series-inca-08-after-shave-perfumed-cologne-400-ml
              - generic [ref=f2e260]:
                - generic [ref=f2e261]: Regular price
                - text: $6.32 AUD
              - generic [ref=f2e262]:
                - button "Sold out ProRapid Tattoo Series Inca 08 After Shave Perfumed Cologne 400 ml" [ref=f2e265] [cursor=pointer]:
                  - generic [ref=f2e266]: QUICK ADD
                  - generic [ref=f2e267]: ›
                - generic [ref=f2e268]: IN STOCK
        - group "5 / 8" [ref=f2e270]:
          - generic [ref=f2e272]:
            - generic [ref=f2e273]:
              - link [ref=f2e275]:
                - /url: /products/prorapid-inca-01-styling-hair-wax-150ml
                - img "ProRapid INCA 01 Styling Hair Wax 150ML" [ref=f2e277]
              - generic:
                - list:
                  - listitem [ref=f2e278]:
                    - generic "Add to wishlist" [ref=f2e280] [cursor=pointer]
            - generic [ref=f2e282]:
              - heading [level=6] [ref=f2e283]:
                - link "ProRapid INCA 01 Styling Hair Wax 150ML" [ref=f2e284]:
                  - /url: /products/prorapid-inca-01-styling-hair-wax-150ml
              - generic [ref=f2e287]:
                - generic [ref=f2e288]: Regular price
                - text: $5.91 AUD
              - generic [ref=f2e289]:
                - button "Sold out ProRapid INCA 01 Styling Hair Wax 150ML" [ref=f2e292] [cursor=pointer]:
                  - generic [ref=f2e293]: QUICK ADD
                  - generic [ref=f2e294]: ›
                - generic [ref=f2e295]: IN STOCK
        - group "6 / 8" [ref=f2e297]:
          - generic [ref=f2e299]:
            - generic [ref=f2e300]:
              - link [ref=f2e302]:
                - /url: /products/prorapid-inca-05-styling-hair-wax-150ml
                - img "ProRapid INCA 05 Styling Hair Wax 150ML" [ref=f2e304]
              - generic:
                - list:
                  - listitem [ref=f2e305]:
                    - generic "Add to wishlist" [ref=f2e307] [cursor=pointer]
            - generic [ref=f2e309]:
              - heading [level=6] [ref=f2e310]:
                - link "ProRapid INCA 05 Styling Hair Wax 150ML" [ref=f2e311]:
                  - /url: /products/prorapid-inca-05-styling-hair-wax-150ml
              - generic [ref=f2e314]:
                - generic [ref=f2e315]: Regular price
                - text: $5.00 AUD
              - generic [ref=f2e316]:
                - button "Sold out ProRapid INCA 05 Styling Hair Wax 150ML" [ref=f2e319] [cursor=pointer]:
                  - generic [ref=f2e320]: QUICK ADD
                  - generic [ref=f2e321]: ›
                - generic [ref=f2e322]: IN STOCK
        - group "7 / 8" [ref=f2e324]:
          - generic [ref=f2e326]:
            - generic [ref=f2e327]:
              - link [ref=f2e329]:
                - /url: /products/prorapid-tattoo-series-inca-05-after-shave-perfumed-cologne-400-ml
                - img "ProRapid Tattoo Series Inca 05 After Shave Perfumed Cologne 400 ml" [ref=f2e331]
              - generic:
                - list:
                  - listitem [ref=f2e332]:
                    - generic "Add to wishlist" [ref=f2e334] [cursor=pointer]
            - generic [ref=f2e336]:
              - heading [level=6] [ref=f2e337]:
                - link "ProRapid Tattoo Series Inca 05 After Shave Perfumed Cologne 400 ml" [ref=f2e338]:
                  - /url: /products/prorapid-tattoo-series-inca-05-after-shave-perfumed-cologne-400-ml
              - generic [ref=f2e341]:
                - generic [ref=f2e342]: Regular price
                - text: $6.32 AUD
              - generic [ref=f2e343]:
                - button "Sold out ProRapid Tattoo Series Inca 05 After Shave Perfumed Cologne 400 ml" [ref=f2e346] [cursor=pointer]:
                  - generic [ref=f2e347]: QUICK ADD
                  - generic [ref=f2e348]: ›
                - generic [ref=f2e349]: IN STOCK
        - group "8 / 8" [ref=f2e351]:
          - generic [ref=f2e353]:
            - generic [ref=f2e354]:
              - link [ref=f2e356]:
                - /url: /products/prorapid-tattoo-series-inca-03-after-shave-perfumed-cologne-400-ml
                - img "ProRapid Tattoo Series Inca 03 After Shave Perfumed Cologne 400 ml" [ref=f2e358]
              - generic:
                - list:
                  - listitem [ref=f2e359]:
                    - generic "Add to wishlist" [ref=f2e361] [cursor=pointer]
            - generic [ref=f2e363]:
              - heading [level=6] [ref=f2e364]:
                - link "ProRapid Tattoo Series Inca 03 After Shave Perfumed Cologne 400 ml" [ref=f2e365]:
                  - /url: /products/prorapid-tattoo-series-inca-03-after-shave-perfumed-cologne-400-ml
              - generic [ref=f2e368]:
                - generic [ref=f2e369]: Regular price
                - text: $6.32 AUD
              - generic [ref=f2e370]:
                - button "Sold out ProRapid Tattoo Series Inca 03 After Shave Perfumed Cologne 400 ml" [ref=f2e373] [cursor=pointer]:
                  - generic [ref=f2e374]: QUICK ADD
                  - generic [ref=f2e375]: ›
                - generic [ref=f2e376]: IN STOCK
      - link "View all products in the ProRapid Men collection" [ref=f2e379] [cursor=pointer]:
        - /url: /collections/prorapid
        - text: View all
    - generic [ref=f2e387]:
      - heading "FEATURED" [level=6] [ref=f2e388]
      - heading "BUILT FOR ALL-DAY HOLD" [level=2] [ref=f2e389]
      - generic [ref=f2e390]: From matte to high-shine — find your finish in the Uppercut range.
      - generic [ref=f2e391]:
        - link "Shop Now" [ref=f2e392] [cursor=pointer]:
          - /url: /collections/hair-products
        - link "View Bundles" [ref=f2e394] [cursor=pointer]:
          - /url: /collections/bundles-kits
    - generic [ref=f2e399]:
      - heading "SINCE 2026 · PRECISION" [level=2] [ref=f2e401]
      - generic [ref=f2e406]:
        - generic [ref=f2e407]:
          - heading "HOW WE DO" [level=6] [ref=f2e408]
          - 'heading "FROM TOOLS TO TECHNIQUE: SHARPEN YOUR ROUTINE" [level=2] [ref=f2e409]'
          - paragraph [ref=f2e410]: From matte to high-shine — find your finish in the Uppercut range.
        - generic [ref=f2e411]:
          - generic [ref=f2e414]:
            - heading "Professional Performance" [level=3] [ref=f2e415]
            - paragraph [ref=f2e416]: Powerful motors and precision blades built to last.
          - generic [ref=f2e419]:
            - heading "Clean Everyday Grooming" [level=3] [ref=f2e420]
            - paragraph [ref=f2e421]: Reliable tools for sharp results at home or in the shop.
        - list [ref=f2e423]:
          - listitem [ref=f2e424]: Built for Barbers
          - listitem [ref=f2e425]: Reliable Accessories
        - link "About ZeroGap" [ref=f2e426] [cursor=pointer]:
          - /url: /pages/about-us
    - generic [ref=f2e431]:
      - generic [ref=f2e432]:
        - heading "WHY ZEROGAP" [level=6] [ref=f2e433]
        - heading "WHY CUSTOMERS CHOOSE ZEROGAP" [level=2] [ref=f2e434]
      - list [ref=f2e436]:
        - listitem [ref=f2e437]:
          - generic [ref=f2e441]:
            - heading "Fast Australia Shipping" [level=4] [ref=f2e442]
            - paragraph [ref=f2e444]: Quick, tracked delivery Australia-wide on every order.
        - listitem [ref=f2e445]:
          - generic [ref=f2e449]:
            - heading "Quality Grooming Tools" [level=4] [ref=f2e450]
            - paragraph [ref=f2e452]: Barber-grade machines and accessories built to perform.
        - listitem [ref=f2e453]:
          - generic [ref=f2e457]:
            - heading "Secure Checkout" [level=4] [ref=f2e458]
            - paragraph [ref=f2e460]: Shopify-secured payments with trusted methods.
        - listitem [ref=f2e461]:
          - generic [ref=f2e465]:
            - heading "Warranty Support" [level=4] [ref=f2e466]
            - paragraph [ref=f2e468]: 12-month warranty and responsive local support.
    - generic [ref=f2e473]:
      - generic [ref=f2e474]:
        - heading "FAQ's" [level=6] [ref=f2e475]
        - heading "Need Guidance? We've Provided" [level=2] [ref=f2e476]
        - paragraph [ref=f2e477]: Answers to the questions we hear most. Still stuck? Our team is here to help.
        - link "View All FAQs" [ref=f2e478] [cursor=pointer]:
          - /url: /pages/faq
      - generic [ref=f2e480]:
        - group [ref=f2e482]:
          - button [expanded] [ref=f2e483] [cursor=pointer]:
            - heading "How do I apply for a trade account?" [level=3] [ref=f2e484]
          - region "How do I apply for a trade account?" [ref=f2e487]:
            - paragraph [ref=f2e488]: Complete the online trade-account application and provide the requested business details. Approval, pricing tier and any payment terms are subject to ZeroGap review and may be changed or withdrawn in accordance with the applicable trade terms.
        - group [ref=f2e490]:
          - button [ref=f2e491] [cursor=pointer]:
            - heading "Are prices shown in Australian dollars?" [level=3] [ref=f2e492]
        - group [ref=f2e496]:
          - button [ref=f2e497] [cursor=pointer]:
            - heading "Who can order from ZeroGap ?" [level=3] [ref=f2e498]
        - group [ref=f2e502]:
          - button [ref=f2e503] [cursor=pointer]:
            - heading "Is there a minimum order?" [level=3] [ref=f2e504]
        - group [ref=f2e508]:
          - button [ref=f2e509] [cursor=pointer]:
            - heading "What happens if an item is out of stock?" [level=3] [ref=f2e510]
        - group [ref=f2e514]:
          - button [ref=f2e515] [cursor=pointer]:
            - heading "How is shipping calculated?" [level=3] [ref=f2e516]
    - generic [ref=f2e523]:
      - generic [ref=f2e524]:
        - heading "GUIDES" [level=6] [ref=f2e525]
        - heading "EXPLORE OUR GROOMING GUIDES" [level=2] [ref=f2e526]
      - list [ref=f2e530]:
        - group "1 / 3" [ref=f2e531]:
          - generic [ref=f2e533]:
            - generic [ref=f2e535]:
              - link [ref=f2e537]:
                - /url: /blogs/news/how-to-pick-your-perfect-pomade-1
                - img "How to Pick Your Perfect Pomade" [ref=f2e538]
              - generic [ref=f2e539]: 01 Aug, 2026
            - generic [ref=f2e541]:
              - generic [ref=f2e542]: Ajit Dadresa
              - heading [level=3] [ref=f2e543]:
                - link "How to Pick Your Perfect Pomade" [ref=f2e544]:
                  - /url: /blogs/news/how-to-pick-your-perfect-pomade-1
              - paragraph [ref=f2e545]: Matte, deluxe or clay — matching finish and hold to your hair.
              - link "Read more" [ref=f2e546] [cursor=pointer]:
                - /url: /blogs/news/how-to-pick-your-perfect-pomade-1
        - group "2 / 3" [ref=f2e548]:
          - generic [ref=f2e550]:
            - generic [ref=f2e552]:
              - link [ref=f2e554]:
                - /url: /blogs/news/beard-oil-vs-balm-what-you-need
                - 'img "Beard Oil vs Balm: What You Need" [ref=f2e555]'
              - generic [ref=f2e556]: 01 Aug, 2026
            - generic [ref=f2e558]:
              - generic [ref=f2e559]: Ajit Dadresa
              - heading [level=3] [ref=f2e560]:
                - 'link "Beard Oil vs Balm: What You Need" [ref=f2e561]':
                  - /url: /blogs/news/beard-oil-vs-balm-what-you-need
              - paragraph [ref=f2e562]: When to use oil, when to use balm, and how to layer both.
              - link "Read more" [ref=f2e563] [cursor=pointer]:
                - /url: /blogs/news/beard-oil-vs-balm-what-you-need
        - group "3 / 3" [ref=f2e565]:
          - generic [ref=f2e567]:
            - generic [ref=f2e569]:
              - link [ref=f2e571]:
                - /url: /blogs/news/how-to-pick-your-perfect-pomade
                - img "How to Pick Your Perfect Pomade" [ref=f2e572]
              - generic [ref=f2e573]: 01 Aug, 2026
            - generic [ref=f2e575]:
              - generic [ref=f2e576]: Ajit Dadresa
              - heading [level=3] [ref=f2e577]:
                - link "How to Pick Your Perfect Pomade" [ref=f2e578]:
                  - /url: /blogs/news/how-to-pick-your-perfect-pomade
              - paragraph [ref=f2e579]: Matte, deluxe or clay — matching finish and hold to your hair.
              - link "Read more" [ref=f2e580] [cursor=pointer]:
                - /url: /blogs/news/how-to-pick-your-perfect-pomade
    - list [ref=f2e589]:
      - group "1 / 5" [ref=f2e590]:
        - link [ref=f2e591] [cursor=pointer]:
          - /url: "#"
      - group "2 / 5" [ref=f2e593]:
        - link [ref=f2e594] [cursor=pointer]:
          - /url: "#"
      - group "3 / 5" [ref=f2e596]:
        - link [ref=f2e597] [cursor=pointer]:
          - /url: "#"
      - group "4 / 5" [ref=f2e599]:
        - link [ref=f2e600] [cursor=pointer]:
          - /url: "#"
      - group "5 / 5" [ref=f2e602]:
        - link [ref=f2e603] [cursor=pointer]:
          - /url: /collections/mousepads
    - generic [ref=f2e609]:
      - paragraph [ref=f2e611]: NEWSLETTER
      - heading "JOIN THE ZEROGAP LIST" [level=2] [ref=f2e612]
      - paragraph [ref=f2e614]: Get grooming tips, product drops, and exclusive offers.
      - generic [ref=f2e618]:
        - textbox "Your email address" [ref=f2e619]
        - button "Subscribe" [ref=f2e620] [cursor=pointer]
  - contentinfo [ref=f2e622]:
    - generic [ref=f2e625]:
      - generic [ref=f2e627]:
        - link:
          - /url: /
        - paragraph [ref=f2e629]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f2e634]:
          - textbox "Your email address" [ref=f2e635]
          - button "Subscribe" [ref=f2e636] [cursor=pointer]
      - generic [ref=f2e637]:
        - heading "Useful links" [level=2] [ref=f2e638]
        - list [ref=f2e639]:
          - listitem [ref=f2e640]:
            - link "Clippers & Electricals" [ref=f2e641] [cursor=pointer]:
              - /url: /collections/clippers-trimmers-shavers
          - listitem [ref=f2e642]:
            - link "Hair Products" [ref=f2e643] [cursor=pointer]:
              - /url: /collections/hair-products
          - listitem [ref=f2e644]:
            - link "Barber Essentials" [ref=f2e645] [cursor=pointer]:
              - /url: /collections/barber-essentials
          - listitem [ref=f2e646]:
            - link "Bundles & Kits" [ref=f2e647] [cursor=pointer]:
              - /url: /collections/bundles-kits
          - listitem [ref=f2e648]:
            - link "Trade Portal" [ref=f2e649] [cursor=pointer]:
              - /url: /pages/trade-portal
      - generic [ref=f2e650]:
        - heading "Help & Support" [level=2] [ref=f2e651]
        - list [ref=f2e652]:
          - listitem [ref=f2e653]:
            - link "About Us" [ref=f2e654] [cursor=pointer]:
              - /url: /pages/about-us
          - listitem [ref=f2e655]:
            - link "Contact" [ref=f2e656] [cursor=pointer]:
              - /url: /pages/contact
          - listitem [ref=f2e657]:
            - link "FAQ" [ref=f2e658] [cursor=pointer]:
              - /url: /pages/faq
          - listitem [ref=f2e659]:
            - link "Shipping" [ref=f2e660] [cursor=pointer]:
              - /url: /pages/shipping-policy
      - generic [ref=f2e661]:
        - heading "Resources" [level=2] [ref=f2e662]
        - list [ref=f2e663]:
          - listitem [ref=f2e664]:
            - link "Returns" [ref=f2e665] [cursor=pointer]:
              - /url: /pages/returns-policy
          - listitem [ref=f2e666]:
            - link "Privacy" [ref=f2e667] [cursor=pointer]:
              - /url: /pages/privacy-policy
          - listitem [ref=f2e668]:
            - link "Terms & Conditions" [ref=f2e669] [cursor=pointer]:
              - /url: /pages/terms-conditions
          - listitem [ref=f2e670]:
            - link "Warranty" [ref=f2e671] [cursor=pointer]:
              - /url: /pages/warranty
      - list [ref=f2e674]:
        - listitem [ref=f2e675]:
          - link "TW" [ref=f2e676] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f2e680]:
          - link "FB" [ref=f2e681] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f2e685]:
          - link "IN" [ref=f2e686] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f2e690]:
          - link "Snapchat" [ref=f2e691] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f2e694]:
          - link "Vimeo" [ref=f2e695] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f2e701]:
      - generic [ref=f2e702]:
        - generic [ref=f2e703]: Payment methods
        - list [ref=f2e704]:
          - listitem [ref=f2e705]:
            - img "American Express" [ref=f2e706]
          - listitem [ref=f2e711]:
            - img "Apple Pay" [ref=f2e712]
          - listitem [ref=f2e723]:
            - img "Google Pay" [ref=f2e724]
          - listitem [ref=f2e732]:
            - img "Mastercard" [ref=f2e733]
          - listitem [ref=f2e740]:
            - img "PayPal" [ref=f2e741]
          - listitem [ref=f2e747]:
            - img "Union Pay" [ref=f2e748]
          - listitem [ref=f2e754]:
            - img "Visa" [ref=f2e755]
      - paragraph [ref=f2e762]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f2e763]:
    - /url: "#zerogap-supply-co"
```

# Test source

```ts
  1  | import { test, expect } from './fixtures';
  2  | 
  3  | const wishlistIcon = (page: import('@playwright/test').Page) =>
  4  |   page.locator('[class*="wishlist"], [aria-label*="wishlist" i], button[data-wishlist]').first();
  5  | 
  6  | test.describe('Home page — wishlist (WL-01..WL-05)', () => {
  7  |   test('WL-01 adding the same item twice does not duplicate it', async ({ unlockedPage: page }) => {
  8  |     const icon = wishlistIcon(page);
  9  |     if (!(await icon.isVisible().catch(() => false))) {
  10 |       test.skip(true, 'No wishlist control detected on Home page for this theme.');
  11 |       return;
  12 |     }
  13 |     await icon.click();
  14 |     await page.waitForTimeout(300);
  15 |     const stateAfterFirst = await icon.getAttribute('aria-pressed').catch(() => null);
  16 |     await icon.click();
  17 |     await page.waitForTimeout(300);
  18 |     const stateAfterSecond = await icon.getAttribute('aria-pressed').catch(() => null);
  19 |     expect(stateAfterFirst).not.toBe(stateAfterSecond === stateAfterFirst ? undefined : stateAfterFirst);
  20 |   });
  21 | 
  22 |   test('WL-02 wishlist as a guest does not throw an error', async ({ unlockedPage: page }) => {
  23 |     const icon = wishlistIcon(page);
  24 |     if (!(await icon.isVisible().catch(() => false))) {
  25 |       test.skip(true, 'No wishlist control detected on Home page for this theme.');
  26 |       return;
  27 |     }
  28 |     const errors: string[] = [];
  29 |     page.on('pageerror', (e) => errors.push(e.message));
  30 |     await icon.click();
  31 |     await page.waitForTimeout(500);
  32 |     expect(errors).toHaveLength(0);
  33 |   });
  34 | 
  35 |   test('WL-05 spam-clicking the toggle leaves a consistent final state', async ({ unlockedPage: page }) => {
  36 |     const icon = wishlistIcon(page);
  37 |     if (!(await icon.isVisible().catch(() => false))) {
  38 |       test.skip(true, 'No wishlist control detected on Home page for this theme.');
  39 |       return;
  40 |     }
  41 |     for (let i = 0; i < 10; i++) {
> 42 |       await icon.click();
     |                  ^ Error: locator.click: Test timeout of 30000ms exceeded.
  43 |     }
  44 |     await page.waitForTimeout(500);
  45 |     await page.reload();
  46 |     // After reload, the icon's persisted state should be readable without error.
  47 |     await expect(icon).toBeVisible();
  48 |   });
  49 | });
  50 | 
```