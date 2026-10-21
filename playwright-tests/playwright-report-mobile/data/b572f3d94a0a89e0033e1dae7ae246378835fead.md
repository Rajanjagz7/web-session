# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: home-wishlist.spec.ts >> Home page — wishlist (WL-01..WL-05) >> WL-01 adding the same item twice does not duplicate it
- Location: tests\home-wishlist.spec.ts:7:7

# Error details

```
Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [ref=f7e1]:
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
  - navigation "breadcrumbs page" [ref=f7e34]:
    - heading "Wishlist" [level=2] [ref=f7e35]
    - link "Home" [ref=f7e36] [cursor=pointer]:
      - /url: /
    - generic [ref=f7e40]: Wishlist
  - main [active] [ref=f7e41]:
    - generic [ref=f7e42]: Your wishlist looks empty
  - contentinfo [ref=f7e48]:
    - generic [ref=f7e51]:
      - generic [ref=f7e53]:
        - link [ref=f7e54] [cursor=pointer]:
          - /url: /
        - paragraph [ref=f7e56]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f7e61]:
          - textbox "Your email address" [ref=f7e62]
          - button "Subscribe" [ref=f7e63] [cursor=pointer]
      - generic [ref=f7e64]:
        - heading "Useful links" [level=2] [ref=f7e65] [cursor=pointer]
        - generic [ref=f7e66] [cursor=pointer]
      - generic [ref=f7e69]:
        - heading "Help & Support" [level=2] [ref=f7e70] [cursor=pointer]
        - generic [ref=f7e71] [cursor=pointer]
      - generic [ref=f7e74]:
        - heading "Resources" [level=2] [ref=f7e75] [cursor=pointer]
        - generic [ref=f7e76] [cursor=pointer]
      - list [ref=f7e81]:
        - listitem [ref=f7e82]:
          - link "TW" [ref=f7e83] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f7e87]:
          - link "FB" [ref=f7e88] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f7e92]:
          - link "IN" [ref=f7e93] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f7e97]:
          - link "Snapchat" [ref=f7e98] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f7e101]:
          - link "Vimeo" [ref=f7e102] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f7e108]:
      - generic [ref=f7e109]:
        - generic [ref=f7e110]: Payment methods
        - list [ref=f7e111]:
          - listitem [ref=f7e112]:
            - img "American Express" [ref=f7e113]
          - listitem [ref=f7e118]:
            - img "Apple Pay" [ref=f7e119]
          - listitem [ref=f7e130]:
            - img "Google Pay" [ref=f7e131]
          - listitem [ref=f7e139]:
            - img "Mastercard" [ref=f7e140]
          - listitem [ref=f7e147]:
            - img "PayPal" [ref=f7e148]
          - listitem [ref=f7e154]:
            - img "Union Pay" [ref=f7e155]
          - listitem [ref=f7e161]:
            - img "Visa" [ref=f7e162]
      - paragraph [ref=f7e169]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f7e170] [cursor=pointer]:
    - /url: "#wishlist"
  - generic [ref=f7e176]:
    - link "Home" [ref=f7e177] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f7e182] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f7e187] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f7e192] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgxMzI4LCJuYmYiOjE3OTI1NzY1Mjh9.kC29LK-xYYCVKs_Us3ouDp8b1wZ3qOMv741Sz7l1nCk
```