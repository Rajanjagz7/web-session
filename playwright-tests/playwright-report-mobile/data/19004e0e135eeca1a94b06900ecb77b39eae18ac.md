# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-wishlist.spec.ts >> Product page — wishlist (PW-01..PW-03) >> PW-01 rapid add/remove toggle ends in a consistent state
- Location: tests\product-wishlist.spec.ts:8:7

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
        - button [ref=f15e24] [cursor=pointer]
  - navigation "breadcrumbs page" [ref=f15e34]:
    - heading "Wishlist" [level=2] [ref=f15e35]
    - link "Home" [ref=f15e36] [cursor=pointer]:
      - /url: /
    - generic [ref=f15e40]: Wishlist
  - main [active] [ref=f15e41]:
    - generic [ref=f15e42]: Your wishlist looks empty
  - contentinfo [ref=f15e48]:
    - generic [ref=f15e51]:
      - generic [ref=f15e53]:
        - link [ref=f15e54] [cursor=pointer]:
          - /url: /
        - paragraph [ref=f15e56]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f15e61]:
          - textbox "Your email address" [ref=f15e62]
          - button "Subscribe" [ref=f15e63] [cursor=pointer]
      - generic [ref=f15e64]:
        - heading "Useful links" [level=2] [ref=f15e65] [cursor=pointer]
        - generic [ref=f15e66] [cursor=pointer]
      - generic [ref=f15e69]:
        - heading "Help & Support" [level=2] [ref=f15e70] [cursor=pointer]
        - generic [ref=f15e71] [cursor=pointer]
      - generic [ref=f15e74]:
        - heading "Resources" [level=2] [ref=f15e75] [cursor=pointer]
        - generic [ref=f15e76] [cursor=pointer]
      - list [ref=f15e81]:
        - listitem [ref=f15e82]:
          - link "TW" [ref=f15e83] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f15e87]:
          - link "FB" [ref=f15e88] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f15e92]:
          - link "IN" [ref=f15e93] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f15e97]:
          - link "Snapchat" [ref=f15e98] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f15e101]:
          - link "Vimeo" [ref=f15e102] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f15e108]:
      - generic [ref=f15e109]:
        - generic [ref=f15e110]: Payment methods
        - list [ref=f15e111]:
          - listitem [ref=f15e112]:
            - img "American Express" [ref=f15e113]
          - listitem [ref=f15e118]:
            - img "Apple Pay" [ref=f15e119]
          - listitem [ref=f15e130]:
            - img "Google Pay" [ref=f15e131]
          - listitem [ref=f15e139]:
            - img "Mastercard" [ref=f15e140]
          - listitem [ref=f15e147]:
            - img "PayPal" [ref=f15e148]
          - listitem [ref=f15e154]:
            - img "Union Pay" [ref=f15e155]
          - listitem [ref=f15e161]:
            - img "Visa" [ref=f15e162]
      - paragraph [ref=f15e169]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f15e170] [cursor=pointer]:
    - /url: "#wishlist"
  - generic [ref=f15e176]:
    - link "Home" [ref=f15e177] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f15e182] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f15e187] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f15e192] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgxMzI4LCJuYmYiOjE3OTI1NzY1Mjh9.kC29LK-xYYCVKs_Us3ouDp8b1wZ3qOMv741Sz7l1nCk
```