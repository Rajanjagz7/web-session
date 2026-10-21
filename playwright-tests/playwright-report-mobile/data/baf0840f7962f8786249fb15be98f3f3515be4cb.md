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
    - generic [ref=f5e39]:
      - img "Cart" [ref=f5e41]
      - heading "Your cart is empty" [level=3] [ref=f5e42]
      - paragraph [ref=f5e43]: Browse our range and add your first product to get started.
      - link "Continue shopping" [ref=f5e44] [cursor=pointer]:
        - /url: /collections/all
  - contentinfo [ref=f5e46]:
    - generic [ref=f5e49]:
      - generic [ref=f5e51]:
        - link [ref=f5e52]:
          - /url: /
        - paragraph [ref=f5e54]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f5e59]:
          - textbox "Your email address" [ref=f5e60]
          - button "Subscribe" [ref=f5e61] [cursor=pointer]
      - generic [ref=f5e62]:
        - heading "Useful links" [level=2] [ref=f5e63]
        - list [ref=f5e64]:
          - listitem [ref=f5e65]:
            - link "Clippers & Electricals" [ref=f5e66] [cursor=pointer]:
              - /url: /collections/clippers-trimmers-shavers
          - listitem [ref=f5e67]:
            - link "Hair Products" [ref=f5e68] [cursor=pointer]:
              - /url: /collections/hair-products
          - listitem [ref=f5e69]:
            - link "Barber Essentials" [ref=f5e70] [cursor=pointer]:
              - /url: /collections/barber-essentials
          - listitem [ref=f5e71]:
            - link "Bundles & Kits" [ref=f5e72] [cursor=pointer]:
              - /url: /collections/bundles-kits
          - listitem [ref=f5e73]:
            - link "Trade Portal" [ref=f5e74] [cursor=pointer]:
              - /url: /pages/trade-portal
      - generic [ref=f5e75]:
        - heading "Help & Support" [level=2] [ref=f5e76]
        - list [ref=f5e77]:
          - listitem [ref=f5e78]:
            - link "About Us" [ref=f5e79] [cursor=pointer]:
              - /url: /pages/about-us
          - listitem [ref=f5e80]:
            - link "Contact" [ref=f5e81] [cursor=pointer]:
              - /url: /pages/contact
          - listitem [ref=f5e82]:
            - link "FAQ" [ref=f5e83] [cursor=pointer]:
              - /url: /pages/faq
          - listitem [ref=f5e84]:
            - link "Shipping" [ref=f5e85] [cursor=pointer]:
              - /url: /pages/shipping-policy
      - generic [ref=f5e86]:
        - heading "Resources" [level=2] [ref=f5e87]
        - list [ref=f5e88]:
          - listitem [ref=f5e89]:
            - link "Returns" [ref=f5e90] [cursor=pointer]:
              - /url: /pages/returns-policy
          - listitem [ref=f5e91]:
            - link "Privacy" [ref=f5e92] [cursor=pointer]:
              - /url: /pages/privacy-policy
          - listitem [ref=f5e93]:
            - link "Terms & Conditions" [ref=f5e94] [cursor=pointer]:
              - /url: /pages/terms-conditions
          - listitem [ref=f5e95]:
            - link "Warranty" [ref=f5e96] [cursor=pointer]:
              - /url: /pages/warranty
      - list [ref=f5e99]:
        - listitem [ref=f5e100]:
          - link "TW" [ref=f5e101] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e103]:
          - link "FB" [ref=f5e104] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e106]:
          - link "IN" [ref=f5e107] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e109]:
          - link "Snapchat" [ref=f5e110] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e112]:
          - link "Vimeo" [ref=f5e113] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f5e118]:
      - generic [ref=f5e119]:
        - generic [ref=f5e120]: Payment methods
        - list [ref=f5e121]:
          - listitem [ref=f5e122]:
            - img "American Express" [ref=f5e123]
          - listitem [ref=f5e128]:
            - img "Apple Pay" [ref=f5e129]
          - listitem [ref=f5e140]:
            - img "Google Pay" [ref=f5e141]
          - listitem [ref=f5e149]:
            - img "Mastercard" [ref=f5e150]
          - listitem [ref=f5e157]:
            - img "PayPal" [ref=f5e158]
          - listitem [ref=f5e164]:
            - img "Union Pay" [ref=f5e165]
          - listitem [ref=f5e171]:
            - img "Visa" [ref=f5e172]
      - paragraph [ref=f5e179]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f5e180]:
    - /url: "#your-shopping-cart"
```