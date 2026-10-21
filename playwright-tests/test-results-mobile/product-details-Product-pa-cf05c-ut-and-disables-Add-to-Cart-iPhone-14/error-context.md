# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-details.spec.ts >> Product page — details (PD-01..PD-05) >> PD-03 an out-of-stock product shows "sold out" and disables Add to Cart
- Location: tests\product-details.spec.ts:25:7

# Error details

```
Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [active] [ref=f5e1]:
  - banner [ref=f5e4]:
    - generic [ref=f5e7]:
      - group [ref=f5e9]:
        - button "Menu" [ref=f5e10] [cursor=pointer]
      - heading [level=1] [ref=f5e13]:
        - link [ref=f5e14] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f5e15]
      - generic [ref=f5e16]:
        - generic [ref=f5e17] [cursor=pointer]
        - link [ref=f5e21] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f5e24] [cursor=pointer]
  - main [ref=f5e31]:
    - navigation "breadcrumbs product" [ref=f5e36]:
      - link "All" [ref=f5e37]:
        - /url: /collections/all
      - generic [ref=f5e41]: Andis Clipper Oil 118ml
    - generic [ref=f5e45]:
      - generic [ref=f5e47]:
        - region "Gallery Viewer" [ref=f5e49]:
          - list [ref=f5e51]:
            - listitem [ref=f5e52]:
              - link [ref=f5e54]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f5e55]
        - generic [ref=f5e57]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f5e59]
          - status [ref=f5e60]:
            - generic [ref=f5e63]:
              - generic [ref=f5e64]: Regular price
              - text: $9.05 AUD
          - generic [ref=f5e65]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f5e66]:
            - paragraph [ref=f5e67]:
              - generic [ref=f5e70]: Hurry! Only 12 left in stock
          - generic [ref=f5e71]:
            - generic [ref=f5e72]:
              - group [ref=f5e74]:
                - button "Share" [ref=f5e75] [cursor=pointer]
              - generic [ref=f5e84]:
                - generic [ref=f5e86]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f5e87] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f5e89]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f5e90] [cursor=pointer]
                - button "Add To Cart" [ref=f5e92] [cursor=pointer]
                - generic "Add to wishlist" [ref=f5e97] [cursor=pointer]
            - generic [ref=f5e99]:
              - generic [ref=f5e100]:
                - paragraph [ref=f5e101]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f5e102]: Ships from Australia in 1–2 business days
              - generic [ref=f5e108]:
                - generic [ref=f5e109]: 12 MONTH WARRANTY
                - generic [ref=f5e110]: Every Andis product is crafted to a premium standard.
      - generic [ref=f5e111]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f5e112]
        - group [ref=f5e113]:
          - heading "Description" [level=3] [ref=f5e116] [cursor=pointer]
      - generic [ref=f5e119]:
        - heading "GOOD TO KNOW" [level=6] [ref=f5e120]
        - group [ref=f5e121]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f5e124] [cursor=pointer]
  - contentinfo [ref=f5e128]:
    - generic [ref=f5e131]:
      - generic [ref=f5e133]:
        - link:
          - /url: /
        - paragraph [ref=f5e135]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f5e140]:
          - textbox "Your email address" [ref=f5e141]
          - button "Subscribe" [ref=f5e142] [cursor=pointer]
      - generic [ref=f5e143]:
        - heading "Useful links" [level=2] [ref=f5e144] [cursor=pointer]
        - generic [ref=f5e145] [cursor=pointer]
      - generic [ref=f5e148]:
        - heading "Help & Support" [level=2] [ref=f5e149] [cursor=pointer]
        - generic [ref=f5e150] [cursor=pointer]
      - generic [ref=f5e153]:
        - heading "Resources" [level=2] [ref=f5e154] [cursor=pointer]
        - generic [ref=f5e155] [cursor=pointer]
      - list [ref=f5e160]:
        - listitem [ref=f5e161]:
          - link "TW" [ref=f5e162] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e166]:
          - link "FB" [ref=f5e167] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e171]:
          - link "IN" [ref=f5e172] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e176]:
          - link "Snapchat" [ref=f5e177] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e180]:
          - link "Vimeo" [ref=f5e181] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f5e187]:
      - generic [ref=f5e188]:
        - generic [ref=f5e189]: Payment methods
        - list [ref=f5e190]:
          - listitem [ref=f5e191]:
            - img "American Express" [ref=f5e192]
          - listitem [ref=f5e197]:
            - img "Apple Pay" [ref=f5e198]
          - listitem [ref=f5e209]:
            - img "Google Pay" [ref=f5e210]
          - listitem [ref=f5e218]:
            - img "Mastercard" [ref=f5e219]
          - listitem [ref=f5e226]:
            - img "PayPal" [ref=f5e227]
          - listitem [ref=f5e233]:
            - img "Union Pay" [ref=f5e234]
          - listitem [ref=f5e240]:
            - img "Visa" [ref=f5e241]
      - paragraph [ref=f5e248]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f5e249]:
    - /url: "#andis-clipper-oil-118ml"
  - generic [ref=f5e255]:
    - link "Home" [ref=f5e256] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f5e261] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f5e266] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f5e271] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgyODk3LCJuYmYiOjE3OTI1NzgwOTd9.xYvok5PZx3INUORDmzTnfmPlGCU1XX1bDtN7WVqiH-E
```