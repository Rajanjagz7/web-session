# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — subtotal (ST-01..ST-04) >> ST-03 subtotal on an empty cart shows $0.00, never NaN
- Location: tests\cart.spec.ts:119:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Tearing down "context" exceeded the test timeout of 30000ms.
```

# Page snapshot

```yaml
- generic [active] [ref=f7e1]:
  - banner [ref=f7e4]:
    - generic [ref=f7e7]:
      - group [ref=f7e9]:
        - button "Menu" [ref=f7e10] [cursor=pointer]
      - heading [level=1] [ref=f7e13]:
        - link [ref=f7e14] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f7e15]
      - generic [ref=f7e16]:
        - generic [ref=f7e17] [cursor=pointer]
        - link [ref=f7e21] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f7e24] [cursor=pointer]
  - main [ref=f7e30]:
    - generic [ref=f7e33]:
      - img "Cart" [ref=f7e35]
      - heading "Your cart is empty" [level=3] [ref=f7e36]
      - paragraph [ref=f7e37]: Browse our range and add your first product to get started.
      - link "Continue shopping" [ref=f7e38] [cursor=pointer]:
        - /url: /collections/all
  - contentinfo [ref=f7e40]:
    - generic [ref=f7e43]:
      - generic [ref=f7e45]:
        - link [ref=f7e46] [cursor=pointer]:
          - /url: /
        - paragraph [ref=f7e48]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f7e53]:
          - textbox "Your email address" [ref=f7e54]
          - button "Subscribe" [ref=f7e55] [cursor=pointer]
      - generic [ref=f7e56]:
        - heading "Useful links" [level=2] [ref=f7e57] [cursor=pointer]
        - generic [ref=f7e58] [cursor=pointer]
      - generic [ref=f7e61]:
        - heading "Help & Support" [level=2] [ref=f7e62] [cursor=pointer]
        - generic [ref=f7e63] [cursor=pointer]
      - generic [ref=f7e66]:
        - heading "Resources" [level=2] [ref=f7e67] [cursor=pointer]
        - generic [ref=f7e68] [cursor=pointer]
      - list [ref=f7e73]:
        - listitem [ref=f7e74]:
          - link "TW" [ref=f7e75] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f7e79]:
          - link "FB" [ref=f7e80] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f7e84]:
          - link "IN" [ref=f7e85] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f7e89]:
          - link "Snapchat" [ref=f7e90] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f7e93]:
          - link "Vimeo" [ref=f7e94] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f7e100]:
      - generic [ref=f7e101]:
        - generic [ref=f7e102]: Payment methods
        - list [ref=f7e103]:
          - listitem [ref=f7e104]:
            - img "American Express" [ref=f7e105]
          - listitem [ref=f7e110]:
            - img "Apple Pay" [ref=f7e111]
          - listitem [ref=f7e122]:
            - img "Google Pay" [ref=f7e123]
          - listitem [ref=f7e131]:
            - img "Mastercard" [ref=f7e132]
          - listitem [ref=f7e139]:
            - img "PayPal" [ref=f7e140]
          - listitem [ref=f7e146]:
            - img "Union Pay" [ref=f7e147]
          - listitem [ref=f7e153]:
            - img "Visa" [ref=f7e154]
      - paragraph [ref=f7e161]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f7e162] [cursor=pointer]:
    - /url: "#your-shopping-cart"
  - generic [ref=f7e168]:
    - link "Home" [ref=f7e169] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f7e174] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f7e179] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f7e184] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgwODA3LCJuYmYiOjE3OTI1NzYwMDd9.Z2V0gswcVRk5qLH2ONzcc0PJMkozhJlEpEoOXPOzBWE
```