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

# Page snapshot

```yaml
- generic [ref=f8e1]:
  - banner [ref=f8e4]:
    - generic [ref=f8e7]:
      - group [ref=f8e9]:
        - button "Menu" [ref=f8e10] [cursor=pointer]
      - heading [level=1] [ref=f8e13]:
        - link [ref=f8e14] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f8e15]
      - generic [ref=f8e16]:
        - generic [ref=f8e17] [cursor=pointer]
        - link [ref=f8e21] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f8e24] [cursor=pointer]
  - main [active] [ref=f8e31]:
    - navigation "breadcrumbs product" [ref=f8e36]:
      - link "All" [ref=f8e37]:
        - /url: /collections/all
      - generic [ref=f8e41]: Andis Clipper Oil 118ml
    - generic [ref=f8e45]:
      - generic [ref=f8e47]:
        - region "Gallery Viewer" [ref=f8e49]:
          - list [ref=f8e51]:
            - listitem [ref=f8e52]:
              - link [ref=f8e54]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f8e55]
        - generic [ref=f8e57]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f8e59]
          - status [ref=f8e60]:
            - generic [ref=f8e63]:
              - generic [ref=f8e64]: Regular price
              - text: $9.05 AUD
          - generic [ref=f8e65]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f8e66]:
            - paragraph [ref=f8e67]:
              - generic [ref=f8e70]: Hurry! Only 12 left in stock
          - generic [ref=f8e71]:
            - generic [ref=f8e72]:
              - group [ref=f8e74]:
                - button "Share" [ref=f8e75] [cursor=pointer]
              - generic [ref=f8e84]:
                - generic [ref=f8e86]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f8e87] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f8e89]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f8e90] [cursor=pointer]
                - button "Add To Cart" [disabled] [ref=f8e92] [cursor=pointer]
                - generic "Add to wishlist" [ref=f8e100] [cursor=pointer]
            - generic [ref=f8e102]:
              - generic [ref=f8e103]:
                - paragraph [ref=f8e104]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f8e105]: Ships from Australia in 1–2 business days
              - generic [ref=f8e111]:
                - generic [ref=f8e112]: 12 MONTH WARRANTY
                - generic [ref=f8e113]: Every Andis product is crafted to a premium standard.
      - generic [ref=f8e114]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f8e115]
        - group [ref=f8e116]:
          - heading "Description" [level=3] [ref=f8e119] [cursor=pointer]
      - generic [ref=f8e122]:
        - heading "GOOD TO KNOW" [level=6] [ref=f8e123]
        - group [ref=f8e124]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f8e127] [cursor=pointer]
  - contentinfo [ref=f8e131]:
    - generic [ref=f8e134]:
      - generic [ref=f8e136]:
        - link:
          - /url: /
        - paragraph [ref=f8e138]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f8e143]:
          - textbox "Your email address" [ref=f8e144]
          - button "Subscribe" [ref=f8e145] [cursor=pointer]
      - generic [ref=f8e146]:
        - heading "Useful links" [level=2] [ref=f8e147] [cursor=pointer]
        - generic [ref=f8e148] [cursor=pointer]
      - generic [ref=f8e151]:
        - heading "Help & Support" [level=2] [ref=f8e152] [cursor=pointer]
        - generic [ref=f8e153] [cursor=pointer]
      - generic [ref=f8e156]:
        - heading "Resources" [level=2] [ref=f8e157] [cursor=pointer]
        - generic [ref=f8e158] [cursor=pointer]
      - list [ref=f8e163]:
        - listitem [ref=f8e164]:
          - link "TW" [ref=f8e165] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f8e169]:
          - link "FB" [ref=f8e170] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f8e174]:
          - link "IN" [ref=f8e175] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f8e179]:
          - link "Snapchat" [ref=f8e180] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f8e183]:
          - link "Vimeo" [ref=f8e184] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f8e190]:
      - generic [ref=f8e191]:
        - generic [ref=f8e192]: Payment methods
        - list [ref=f8e193]:
          - listitem [ref=f8e194]:
            - img "American Express" [ref=f8e195]
          - listitem [ref=f8e200]:
            - img "Apple Pay" [ref=f8e201]
          - listitem [ref=f8e212]:
            - img "Google Pay" [ref=f8e213]
          - listitem [ref=f8e221]:
            - img "Mastercard" [ref=f8e222]
          - listitem [ref=f8e229]:
            - img "PayPal" [ref=f8e230]
          - listitem [ref=f8e236]:
            - img "Union Pay" [ref=f8e237]
          - listitem [ref=f8e243]:
            - img "Visa" [ref=f8e244]
      - paragraph [ref=f8e251]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f8e252]:
    - /url: "#andis-clipper-oil-118ml"
  - generic [ref=f8e258]:
    - link "Home" [ref=f8e259] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f8e264] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f8e269] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f8e274] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgyODk3LCJuYmYiOjE3OTI1NzgwOTd9.xYvok5PZx3INUORDmzTnfmPlGCU1XX1bDtN7WVqiH-E
```