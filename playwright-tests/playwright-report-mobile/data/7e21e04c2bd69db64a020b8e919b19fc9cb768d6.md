# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-cart.spec.ts >> Product page — add to cart (PA-01..PA-08) >> PA-03 decimal quantity is rejected or rounded, never silently accepted as-is
- Location: tests\product-cart.spec.ts:38:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: expected decimal input to be rounded to a whole number

expect(received).toBeTruthy()

Received: false
```

```
Tearing down "context" exceeded the test timeout of 30000ms.
```

# Page snapshot

```yaml
- generic [ref=f11e1]:
  - banner [ref=f11e4]:
    - generic [ref=f11e7]:
      - group [ref=f11e9]:
        - button "Menu" [ref=f11e10] [cursor=pointer]
      - heading [level=1] [ref=f11e13]:
        - link [ref=f11e14] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f11e15]
      - generic [ref=f11e16]:
        - generic [ref=f11e17] [cursor=pointer]
        - link [ref=f11e21] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f11e24] [cursor=pointer]
  - main [ref=f11e30]:
    - navigation "breadcrumbs product" [ref=f11e35]:
      - link "All" [ref=f11e36] [cursor=pointer]:
        - /url: /collections/all
      - generic [ref=f11e40]: Andis Clipper Oil 118ml
    - generic [ref=f11e44]:
      - generic [ref=f11e46]:
        - region "Gallery Viewer" [ref=f11e48]:
          - list [ref=f11e50]:
            - listitem [ref=f11e51]:
              - link [ref=f11e53] [cursor=pointer]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f11e54]
        - generic [ref=f11e56]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f11e58]
          - status [ref=f11e59]:
            - generic [ref=f11e62]:
              - generic [ref=f11e63]: Regular price
              - text: $9.05 AUD
          - generic [ref=f11e64]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f11e65]:
            - paragraph [ref=f11e66]:
              - generic [ref=f11e69]: Hurry! Only 12 left in stock
          - generic [ref=f11e70]:
            - generic [ref=f11e71]:
              - group [ref=f11e73]:
                - button "Share" [ref=f11e74] [cursor=pointer]
              - generic [ref=f11e83]:
                - generic [ref=f11e84]:
                  - generic [ref=f11e85]:
                    - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f11e86] [cursor=pointer]
                    - spinbutton "Quantity" [active] [invalid] [ref=f11e88]: "2.5"
                    - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f11e89] [cursor=pointer]
                  - alert [ref=f11e91]: Quantity must be a whole number (no decimals).
                - button "Add To Cart" [disabled] [ref=f11e92] [cursor=pointer]
                - generic "Add to wishlist" [ref=f11e97] [cursor=pointer]
            - generic [ref=f11e99]:
              - generic [ref=f11e100]:
                - paragraph [ref=f11e101]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f11e102]: Ships from Australia in 1–2 business days
              - generic [ref=f11e108]:
                - generic [ref=f11e109]: 12 MONTH WARRANTY
                - generic [ref=f11e110]: Every Andis product is crafted to a premium standard.
      - generic [ref=f11e111]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f11e112]
        - group [ref=f11e113]:
          - heading "Description" [level=3] [ref=f11e116] [cursor=pointer]
      - generic [ref=f11e119]:
        - heading "GOOD TO KNOW" [level=6] [ref=f11e120]
        - group [ref=f11e121]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f11e124] [cursor=pointer]
  - contentinfo [ref=f11e128]:
    - generic [ref=f11e131]:
      - generic [ref=f11e133]:
        - link [ref=f11e134] [cursor=pointer]:
          - /url: /
        - paragraph [ref=f11e136]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f11e141]:
          - textbox "Your email address" [ref=f11e142]
          - button "Subscribe" [ref=f11e143] [cursor=pointer]
      - generic [ref=f11e144]:
        - heading "Useful links" [level=2] [ref=f11e145] [cursor=pointer]
        - generic [ref=f11e146] [cursor=pointer]
      - generic [ref=f11e149]:
        - heading "Help & Support" [level=2] [ref=f11e150] [cursor=pointer]
        - generic [ref=f11e151] [cursor=pointer]
      - generic [ref=f11e154]:
        - heading "Resources" [level=2] [ref=f11e155] [cursor=pointer]
        - generic [ref=f11e156] [cursor=pointer]
      - list [ref=f11e161]:
        - listitem [ref=f11e162]:
          - link "TW" [ref=f11e163] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e167]:
          - link "FB" [ref=f11e168] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e172]:
          - link "IN" [ref=f11e173] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e177]:
          - link "Snapchat" [ref=f11e178] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e181]:
          - link "Vimeo" [ref=f11e182] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f11e188]:
      - generic [ref=f11e189]:
        - generic [ref=f11e190]: Payment methods
        - list [ref=f11e191]:
          - listitem [ref=f11e192]:
            - img "American Express" [ref=f11e193]
          - listitem [ref=f11e198]:
            - img "Apple Pay" [ref=f11e199]
          - listitem [ref=f11e210]:
            - img "Google Pay" [ref=f11e211]
          - listitem [ref=f11e219]:
            - img "Mastercard" [ref=f11e220]
          - listitem [ref=f11e227]:
            - img "PayPal" [ref=f11e228]
          - listitem [ref=f11e234]:
            - img "Union Pay" [ref=f11e235]
          - listitem [ref=f11e241]:
            - img "Visa" [ref=f11e242]
      - paragraph [ref=f11e249]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f11e250] [cursor=pointer]:
    - /url: "#andis-clipper-oil-118ml"
  - generic [ref=f11e256]:
    - link "Home" [ref=f11e257] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f11e262] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f11e267] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f11e272] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgxMDAzLCJuYmYiOjE3OTI1NzYyMDN9.hv0KCcg2EYyleY9rt8PK7SMgVjauoqGjJTuNWRbYB14
```