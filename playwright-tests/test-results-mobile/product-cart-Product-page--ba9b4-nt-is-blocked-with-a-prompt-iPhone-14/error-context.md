# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-cart.spec.ts >> Product page — add to cart (PA-01..PA-08) >> PA-07 add without selecting a required variant is blocked with a prompt
- Location: tests\product-cart.spec.ts:67:7

# Error details

```
Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [active] [ref=f7e1]:
  - banner [ref=f7e5]:
    - generic [ref=f7e8]:
      - group [ref=f7e10]:
        - generic "Menu" [ref=f7e11] [cursor=pointer]
      - heading [level=1] [ref=f7e14]:
        - link [ref=f7e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f7e16]
      - generic [ref=f7e17]:
        - generic [ref=f7e18] [cursor=pointer]
        - link [ref=f7e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - link [ref=f7e26] [cursor=pointer]:
          - /url: /cart
  - main [ref=f7e33]:
    - navigation "breadcrumbs product" [ref=f7e38]:
      - link "All" [ref=f7e39]:
        - /url: /collections/all
      - generic [ref=f7e43]: Andis Clipper Oil 118ml
    - generic [ref=f7e47]:
      - generic [ref=f7e49]:
        - region "Gallery Viewer" [ref=f7e51]:
          - list [ref=f7e53]:
            - listitem [ref=f7e54]:
              - link [ref=f7e56]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f7e57]
        - generic [ref=f7e59]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f7e61]
          - status [ref=f7e62]:
            - generic [ref=f7e65]:
              - generic [ref=f7e66]: Regular price
              - text: $9.05 AUD
          - generic [ref=f7e67]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f7e68]:
            - paragraph [ref=f7e69]:
              - generic [ref=f7e72]: Hurry! Only 12 left in stock
          - generic [ref=f7e73]:
            - generic [ref=f7e74]:
              - group [ref=f7e76]:
                - generic "Share" [ref=f7e77] [cursor=pointer]
              - generic [ref=f7e86]:
                - generic [ref=f7e88]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f7e89] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f7e91]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f7e92] [cursor=pointer]
                - button "Add To Cart" [ref=f7e94] [cursor=pointer]
                - generic "Add to wishlist" [ref=f7e99] [cursor=pointer]
            - generic [ref=f7e101]:
              - generic [ref=f7e102]:
                - paragraph [ref=f7e103]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f7e104]: Ships from Australia in 1–2 business days
              - generic [ref=f7e110]:
                - generic [ref=f7e111]: 12 MONTH WARRANTY
                - generic [ref=f7e112]: Every Andis product is crafted to a premium standard.
      - generic [ref=f7e113]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f7e114]
        - group [ref=f7e115]:
          - heading "Description" [level=3] [ref=f7e118] [cursor=pointer]
      - generic [ref=f7e121]:
        - heading "GOOD TO KNOW" [level=6] [ref=f7e122]
        - group [ref=f7e123]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f7e126] [cursor=pointer]
```