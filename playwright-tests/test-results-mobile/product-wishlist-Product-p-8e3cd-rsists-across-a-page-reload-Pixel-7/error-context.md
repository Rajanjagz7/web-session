# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-wishlist.spec.ts >> Product page — wishlist (PW-01..PW-03) >> PW-03 wishlist state persists across a page reload
- Location: tests\product-wishlist.spec.ts:35:7

# Error details

```
Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [active] [ref=f19e1]:
  - banner [ref=f19e4]:
    - generic [ref=f19e7]:
      - group [ref=f19e9]:
        - button "Menu" [ref=f19e10] [cursor=pointer]
      - heading [level=1] [ref=f19e13]:
        - link [ref=f19e14] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f19e15]
      - generic [ref=f19e16]:
        - generic [ref=f19e17] [cursor=pointer]
        - link [ref=f19e21] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f19e24] [cursor=pointer]
  - navigation "breadcrumbs page" [ref=f19e34]:
    - heading "Wishlist" [level=2] [ref=f19e35]
    - link "Home" [ref=f19e36] [cursor=pointer]:
      - /url: /
    - generic [ref=f19e40]: Wishlist
  - main [ref=f19e41]:
    - generic [ref=f19e42]: Your wishlist looks empty
  - contentinfo [ref=f19e48]:
    - generic [ref=f19e51]:
      - generic [ref=f19e53]:
        - link [ref=f19e54] [cursor=pointer]:
          - /url: /
        - paragraph [ref=f19e56]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f19e61]:
          - textbox "Your email address" [ref=f19e62]
          - button "Subscribe" [ref=f19e63] [cursor=pointer]
      - generic [ref=f19e64]:
        - heading "Useful links" [level=2] [ref=f19e65] [cursor=pointer]
        - generic [ref=f19e66] [cursor=pointer]
      - generic [ref=f19e69]:
        - heading "Help & Support" [level=2] [ref=f19e70] [cursor=pointer]
        - generic [ref=f19e71] [cursor=pointer]
      - generic [ref=f19e74]:
        - heading "Resources" [level=2] [ref=f19e75] [cursor=pointer]
        - generic [ref=f19e76] [cursor=pointer]
      - list [ref=f19e81]:
        - listitem [ref=f19e82]:
          - link "TW" [ref=f19e83] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f19e87]:
          - link "FB" [ref=f19e88] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f19e92]:
          - link "IN" [ref=f19e93] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f19e97]:
          - link "Snapchat" [ref=f19e98] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f19e101]:
          - link "Vimeo" [ref=f19e102] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f19e108]:
      - generic [ref=f19e109]:
        - generic [ref=f19e110]: Payment methods
        - list [ref=f19e111]:
          - listitem [ref=f19e112]:
            - img "American Express" [ref=f19e113]
          - listitem [ref=f19e118]:
            - img "Apple Pay" [ref=f19e119]
          - listitem [ref=f19e130]:
            - img "Google Pay" [ref=f19e131]
          - listitem [ref=f19e139]:
            - img "Mastercard" [ref=f19e140]
          - listitem [ref=f19e147]:
            - img "PayPal" [ref=f19e148]
          - listitem [ref=f19e154]:
            - img "Union Pay" [ref=f19e155]
          - listitem [ref=f19e161]:
            - img "Visa" [ref=f19e162]
      - paragraph [ref=f19e169]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f19e170] [cursor=pointer]:
    - /url: "#wishlist"
  - generic [ref=f19e176]:
    - link "Home" [ref=f19e177] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f19e182] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f19e187] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f19e192] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgxMzI4LCJuYmYiOjE3OTI1NzY1Mjh9.kC29LK-xYYCVKs_Us3ouDp8b1wZ3qOMv741Sz7l1nCk
```