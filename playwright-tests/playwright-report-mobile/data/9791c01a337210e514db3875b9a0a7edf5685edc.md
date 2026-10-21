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
  - banner [ref=f5e5]:
    - generic [ref=f5e8]:
      - group [ref=f5e10]:
        - button "Menu" [ref=f5e11] [cursor=pointer]
      - heading [level=1] [ref=f5e14]:
        - link [ref=f5e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f5e16]
      - generic [ref=f5e17]:
        - generic [ref=f5e18] [cursor=pointer]
        - link [ref=f5e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f5e25] [cursor=pointer]
        - link [ref=f5e32] [cursor=pointer]:
          - /url: /account
  - main [ref=f5e36]:
    - generic [ref=f5e38]:
      - heading "404" [level=2] [ref=f5e39]
      - heading "You’re lost" [level=6] [ref=f5e40]
      - heading "Game Over! Page Not Found." [level=1] [ref=f5e41]
      - paragraph [ref=f5e42]: You didn't break the internet, but we can't find what you are looking for.
      - link "Back To Home" [ref=f5e43] [cursor=pointer]:
        - /url: /
  - contentinfo [ref=f5e45]:
    - generic [ref=f5e48]:
      - paragraph [ref=f5e52]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
      - generic [ref=f5e58]:
        - heading "Useful links" [level=2] [ref=f5e59]
        - list [ref=f5e60]:
          - listitem [ref=f5e61]
          - listitem [ref=f5e62]
          - listitem [ref=f5e63]
          - listitem [ref=f5e64]
          - listitem [ref=f5e65]
      - generic [ref=f5e66]:
        - heading "Help & Support" [level=2] [ref=f5e67]
        - list [ref=f5e68]:
          - listitem [ref=f5e69]
          - listitem [ref=f5e70]
          - listitem [ref=f5e71]
          - listitem [ref=f5e72]
      - generic [ref=f5e73]:
        - heading "Resources" [level=2] [ref=f5e74]
        - list [ref=f5e75]:
          - listitem [ref=f5e76]
          - listitem [ref=f5e77]
          - listitem [ref=f5e78]
          - listitem [ref=f5e79]
      - list [ref=f5e82]:
        - listitem [ref=f5e83]
        - listitem [ref=f5e84]
        - listitem [ref=f5e85]
        - listitem [ref=f5e86]
        - listitem [ref=f5e87]
    - generic [ref=f5e91]:
      - generic [ref=f5e92]:
        - generic [ref=f5e93]: Payment methods
        - list [ref=f5e94]:
          - listitem [ref=f5e95]:
            - img "American Express" [ref=f5e96]
          - listitem [ref=f5e101]:
            - img "Apple Pay" [ref=f5e102]
          - listitem [ref=f5e113]:
            - img "Google Pay" [ref=f5e114]
          - listitem [ref=f5e122]:
            - img "Mastercard" [ref=f5e123]
          - listitem [ref=f5e130]:
            - img "PayPal" [ref=f5e131]
          - listitem [ref=f5e137]:
            - img "Union Pay" [ref=f5e138]
          - listitem [ref=f5e144]:
            - img "Visa" [ref=f5e145]
      - paragraph [ref=f5e152]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f5e153]:
    - /url: "#404-not-found"
```