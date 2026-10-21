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

# Page snapshot

```yaml
- generic [active] [ref=f11e1]:
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
  - navigation "breadcrumbs page" [ref=f11e34]:
    - heading "Wishlist" [level=2] [ref=f11e35]
    - link "Home" [ref=f11e36] [cursor=pointer]:
      - /url: /
    - generic [ref=f11e40]: Wishlist
  - main [ref=f11e41]:
    - generic [ref=f11e42]: Your wishlist looks empty
  - contentinfo [ref=f11e48]:
    - generic [ref=f11e51]:
      - generic [ref=f11e53]:
        - link [ref=f11e54] [cursor=pointer]:
          - /url: /
        - paragraph [ref=f11e56]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f11e61]:
          - textbox "Your email address" [ref=f11e62]
          - button "Subscribe" [ref=f11e63] [cursor=pointer]
      - generic [ref=f11e64]:
        - heading "Useful links" [level=2] [ref=f11e65] [cursor=pointer]
        - generic [ref=f11e66] [cursor=pointer]
      - generic [ref=f11e69]:
        - heading "Help & Support" [level=2] [ref=f11e70] [cursor=pointer]
        - generic [ref=f11e71] [cursor=pointer]
      - generic [ref=f11e74]:
        - heading "Resources" [level=2] [ref=f11e75] [cursor=pointer]
        - generic [ref=f11e76] [cursor=pointer]
      - list [ref=f11e81]:
        - listitem [ref=f11e82]:
          - link "TW" [ref=f11e83] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e87]:
          - link "FB" [ref=f11e88] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e92]:
          - link "IN" [ref=f11e93] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e97]:
          - link "Snapchat" [ref=f11e98] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e101]:
          - link "Vimeo" [ref=f11e102] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f11e108]:
      - generic [ref=f11e109]:
        - generic [ref=f11e110]: Payment methods
        - list [ref=f11e111]:
          - listitem [ref=f11e112]:
            - img "American Express" [ref=f11e113]
          - listitem [ref=f11e118]:
            - img "Apple Pay" [ref=f11e119]
          - listitem [ref=f11e130]:
            - img "Google Pay" [ref=f11e131]
          - listitem [ref=f11e139]:
            - img "Mastercard" [ref=f11e140]
          - listitem [ref=f11e147]:
            - img "PayPal" [ref=f11e148]
          - listitem [ref=f11e154]:
            - img "Union Pay" [ref=f11e155]
          - listitem [ref=f11e161]:
            - img "Visa" [ref=f11e162]
      - paragraph [ref=f11e169]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f11e170] [cursor=pointer]:
    - /url: "#wishlist"
  - generic [ref=f11e176]:
    - link "Home" [ref=f11e177] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f11e182] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f11e187] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f11e192] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgxMzI4LCJuYmYiOjE3OTI1NzY1Mjh9.kC29LK-xYYCVKs_Us3ouDp8b1wZ3qOMv741Sz7l1nCk
```