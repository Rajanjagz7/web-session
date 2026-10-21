# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-cart.spec.ts >> Product page — add to cart (PA-01..PA-08) >> PA-08 rapid double-click does not duplicate the line item
- Location: tests\product-cart.spec.ts:85:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Tearing down "context" exceeded the test timeout of 30000ms.
```

# Page snapshot

```yaml
- generic [active] [ref=f15e1]:
  - banner [ref=f15e5]:
    - generic [ref=f15e8]:
      - group [ref=f15e10]:
        - button "Menu" [ref=f15e11] [cursor=pointer]
      - heading [level=1] [ref=f15e14]:
        - link [ref=f15e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f15e16]
      - generic [ref=f15e17]:
        - generic [ref=f15e18] [cursor=pointer]
        - link [ref=f15e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - button "1 item" [ref=f15e25] [cursor=pointer]:
          - generic [ref=f15e31]:
            - generic [ref=f15e32]: "1"
            - generic [ref=f15e33]: 1 item
  - main [ref=f15e34]:
    - navigation "breadcrumbs cart" [ref=f15e39]:
      - heading "Your Shopping Cart" [level=2] [ref=f15e40]
    - generic [ref=f15e42]:
      - heading "Cart" [level=1] [ref=f15e44]
      - generic [ref=f15e45]:
        - table [ref=f15e48]:
          - caption [ref=f15e49]: Cart
          - rowgroup [ref=f15e50]:
            - row [ref=f15e51]:
              - cell [ref=f15e52]:
                - link [ref=f15e53] [cursor=pointer]:
                  - /url: /products/andis-clipper-oil-118ml?variant=45211104084037
                - img "Andis Clipper Oil 118ml" [ref=f15e55]
              - cell "Andis Clipper Oil 118ml $9.05" [ref=f15e56]:
                - link "Andis Clipper Oil 118ml" [ref=f15e57] [cursor=pointer]:
                  - /url: /products/andis-clipper-oil-118ml?variant=45211104084037
                - generic [ref=f15e58]: $9.05
              - cell "Quantity Decrease quantity for Andis Clipper Oil 118ml 1 Increase quantity for Andis Clipper Oil 118ml" [ref=f15e59]:
                - generic [ref=f15e60]:
                  - generic [ref=f15e61]: Quantity
                  - generic [ref=f15e62]:
                    - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f15e63] [cursor=pointer]
                    - spinbutton "Quantity for Andis Clipper Oil 118ml" [ref=f15e65]: "1"
                    - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f15e66] [cursor=pointer]
                - alert
              - cell [ref=f15e68]:
                - link "Remove Andis Clipper Oil 118ml" [ref=f15e71] [cursor=pointer]:
                  - /url: /cart/change?id=45211104084037:52a38e27dde3abfa19d6dcee03b277c3&quantity=0
                  - text: X
        - status [ref=f15e72]: Loading...
      - link "Continue shopping" [ref=f15e74] [cursor=pointer]:
        - /url: /collections/all
    - generic [ref=f15e79]:
      - generic [ref=f15e80]:
        - generic [ref=f15e81]:
          - heading "Subtotal" [level=2] [ref=f15e82]
          - paragraph [ref=f15e83]: $9.05 AUD
        - generic [ref=f15e84]: Taxes and shipping calculated at checkout
      - generic [ref=f15e86]:
        - textbox "Enter Your Discount Code" [ref=f15e87]
        - button "Apply" [ref=f15e88] [cursor=pointer]
      - button "Check out" [ref=f15e90] [cursor=pointer]
  - link "To top" [ref=f15e92] [cursor=pointer]:
    - /url: "#your-shopping-cart"
  - generic [ref=f15e98]:
    - link "Home" [ref=f15e99] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f15e104] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f15e109] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f15e114] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgxMDU0LCJuYmYiOjE3OTI1NzYyNTR9.ljjPl--s6WZzXxXgsZ-Epk-4crV1N3seT9Aiy7FZP3w
```