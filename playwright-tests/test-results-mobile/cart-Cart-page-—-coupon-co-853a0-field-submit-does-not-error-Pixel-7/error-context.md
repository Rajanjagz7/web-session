# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — coupon code (CP-01..CP-10) >> CP-01 empty coupon field submit does not error
- Location: tests\cart.spec.ts:126:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Tearing down "context" exceeded the test timeout of 30000ms.
```

# Page snapshot

```yaml
- generic [ref=f15e1]:
  - banner [ref=f15e4]:
    - generic [ref=f15e7]:
      - group [ref=f15e9]:
        - button "Menu" [ref=f15e10] [cursor=pointer]
      - heading [level=1] [ref=f15e13]:
        - link [ref=f15e14] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f15e15]
      - generic [ref=f15e16]:
        - generic [ref=f15e17] [cursor=pointer]
        - link [ref=f15e21] [cursor=pointer]:
          - /url: /pages/wishlist
        - button "1 item" [ref=f15e24] [cursor=pointer]:
          - generic [ref=f15e30]:
            - generic [ref=f15e31]: "1"
            - generic [ref=f15e32]: 1 item
  - main [ref=f15e33]:
    - navigation "breadcrumbs cart" [ref=f15e38]:
      - heading "Your Shopping Cart" [level=2] [ref=f15e39]
    - generic [ref=f15e41]:
      - heading "Cart" [level=1] [ref=f15e43]
      - generic [ref=f15e44]:
        - table [ref=f15e47]:
          - caption [ref=f15e48]: Cart
          - rowgroup [ref=f15e49]:
            - row [ref=f15e50]:
              - cell [ref=f15e51]:
                - link [ref=f15e52] [cursor=pointer]:
                  - /url: /products/andis-clipper-oil-118ml?variant=45211104084037
                - img "Andis Clipper Oil 118ml" [ref=f15e54]
              - cell "Andis Clipper Oil 118ml $9.05" [ref=f15e55]:
                - link "Andis Clipper Oil 118ml" [ref=f15e56] [cursor=pointer]:
                  - /url: /products/andis-clipper-oil-118ml?variant=45211104084037
                - generic [ref=f15e57]: $9.05
              - cell "Quantity Decrease quantity for Andis Clipper Oil 118ml 1 Increase quantity for Andis Clipper Oil 118ml" [ref=f15e58]:
                - generic [ref=f15e59]:
                  - generic [ref=f15e60]: Quantity
                  - generic [ref=f15e61]:
                    - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f15e62] [cursor=pointer]
                    - spinbutton "Quantity for Andis Clipper Oil 118ml" [ref=f15e64]: "1"
                    - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f15e65] [cursor=pointer]
                - alert
              - cell [ref=f15e67]:
                - link "Remove Andis Clipper Oil 118ml" [ref=f15e70] [cursor=pointer]:
                  - /url: /cart/change?id=45211104084037:52a38e27dde3abfa19d6dcee03b277c3&quantity=0
                  - text: X
        - status [ref=f15e71]: Loading...
      - link "Continue shopping" [ref=f15e73] [cursor=pointer]:
        - /url: /collections/all
    - generic [ref=f15e78]:
      - generic [ref=f15e79]:
        - generic [ref=f15e80]:
          - heading "Subtotal" [level=2] [ref=f15e81]
          - paragraph [ref=f15e82]: $9.05 AUD
        - generic [ref=f15e83]: Taxes and shipping calculated at checkout
      - generic [ref=f15e85]:
        - textbox "Enter Your Discount Code" [active] [ref=f15e86]
        - button "Apply" [ref=f15e87] [cursor=pointer]
      - button "Check out" [ref=f15e89] [cursor=pointer]
  - contentinfo [ref=f15e91]:
    - generic [ref=f15e94]:
      - generic [ref=f15e96]:
        - link [ref=f15e97] [cursor=pointer]:
          - /url: /
        - paragraph [ref=f15e99]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f15e104]:
          - textbox "Your email address" [ref=f15e105]
          - button "Subscribe" [ref=f15e106] [cursor=pointer]
      - generic [ref=f15e107]:
        - heading "Useful links" [level=2] [ref=f15e108] [cursor=pointer]
        - generic [ref=f15e109] [cursor=pointer]
      - generic [ref=f15e112]:
        - heading "Help & Support" [level=2] [ref=f15e113] [cursor=pointer]
        - generic [ref=f15e114] [cursor=pointer]
      - generic [ref=f15e117]:
        - heading "Resources" [level=2] [ref=f15e118] [cursor=pointer]
        - generic [ref=f15e119] [cursor=pointer]
      - list [ref=f15e124]:
        - listitem [ref=f15e125]:
          - link "TW" [ref=f15e126] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f15e130]:
          - link "FB" [ref=f15e131] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f15e135]:
          - link "IN" [ref=f15e136] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f15e140]:
          - link "Snapchat" [ref=f15e141] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f15e144]:
          - link "Vimeo" [ref=f15e145] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f15e151]:
      - generic [ref=f15e152]:
        - generic [ref=f15e153]: Payment methods
        - list [ref=f15e154]:
          - listitem [ref=f15e155]:
            - img "American Express" [ref=f15e156]
          - listitem [ref=f15e161]:
            - img "Apple Pay" [ref=f15e162]
          - listitem [ref=f15e173]:
            - img "Google Pay" [ref=f15e174]
          - listitem [ref=f15e182]:
            - img "Mastercard" [ref=f15e183]
          - listitem [ref=f15e190]:
            - img "PayPal" [ref=f15e191]
          - listitem [ref=f15e197]:
            - img "Union Pay" [ref=f15e198]
          - listitem [ref=f15e204]:
            - img "Visa" [ref=f15e205]
      - paragraph [ref=f15e212]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f15e213] [cursor=pointer]:
    - /url: "#your-shopping-cart"
  - generic [ref=f15e219]:
    - link "Home" [ref=f15e220] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f15e225] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f15e230] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f15e235] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgwODI4LCJuYmYiOjE3OTI1NzYwMjh9.rSTMqZhI6tgRi-Yu3P3ajZ4pdeL9vQQJMl0t7Rl1mMg
```