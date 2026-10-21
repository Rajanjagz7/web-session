# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: home-blog.spec.ts >> Home page — blog posts (BL-01..BL-04) >> BL-04 nonexistent blog post URL returns a themed 404, not a raw error
- Location: tests\home-blog.spec.ts:32:7

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
    - generic [ref=f5e33]:
      - heading "404" [level=2] [ref=f5e34]
      - heading "You’re lost" [level=6] [ref=f5e35]
      - heading "Game Over! Page Not Found." [level=1] [ref=f5e36]
      - paragraph [ref=f5e37]: You didn't break the internet, but we can't find what you are looking for.
      - link "Back To Home" [ref=f5e38] [cursor=pointer]:
        - /url: /
  - contentinfo [ref=f5e40]:
    - generic [ref=f5e43]:
      - generic [ref=f5e45]:
        - link [ref=f5e46]:
          - /url: /
        - paragraph [ref=f5e48]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f5e53]:
          - textbox "Your email address" [ref=f5e54]
          - button "Subscribe" [ref=f5e55] [cursor=pointer]
      - generic [ref=f5e56]:
        - heading "Useful links" [level=2] [ref=f5e57] [cursor=pointer]
        - generic [ref=f5e58] [cursor=pointer]
      - generic [ref=f5e61]:
        - heading "Help & Support" [level=2] [ref=f5e62] [cursor=pointer]
        - generic [ref=f5e63] [cursor=pointer]
      - generic [ref=f5e66]:
        - heading "Resources" [level=2] [ref=f5e67] [cursor=pointer]
        - generic [ref=f5e68] [cursor=pointer]
      - list [ref=f5e73]:
        - listitem [ref=f5e74]:
          - link "TW" [ref=f5e75] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e79]:
          - link "FB" [ref=f5e80] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e84]:
          - link "IN" [ref=f5e85] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e89]:
          - link "Snapchat" [ref=f5e90] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e93]:
          - link "Vimeo" [ref=f5e94] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f5e100]:
      - generic [ref=f5e101]:
        - generic [ref=f5e102]: Payment methods
        - list [ref=f5e103]:
          - listitem [ref=f5e104]:
            - img "American Express" [ref=f5e105]
          - listitem [ref=f5e110]:
            - img "Apple Pay" [ref=f5e111]
          - listitem [ref=f5e122]:
            - img "Google Pay" [ref=f5e123]
          - listitem [ref=f5e131]:
            - img "Mastercard" [ref=f5e132]
          - listitem [ref=f5e139]:
            - img "PayPal" [ref=f5e140]
          - listitem [ref=f5e146]:
            - img "Union Pay" [ref=f5e147]
          - listitem [ref=f5e153]:
            - img "Visa" [ref=f5e154]
      - paragraph [ref=f5e161]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f5e162]:
    - /url: "#404-not-found"
  - generic [ref=f5e168]:
    - link "Home" [ref=f5e169] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f5e174] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f5e179] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f5e184] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgzMDEzLCJuYmYiOjE3OTI1NzgyMTN9.tD0B2TLgVVPNn0FfK9DQoJEc6iVzjorV3Jq-PreyyVU
```