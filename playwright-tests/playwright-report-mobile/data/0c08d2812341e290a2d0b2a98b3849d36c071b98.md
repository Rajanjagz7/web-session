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
- dialog "Search" [ref=f7e5]:
  - generic [ref=f7e7]:
    - button "Close" [ref=f7e8] [cursor=pointer]
    - search [ref=f7e15]:
      - heading "What are you looking for ?" [level=2] [ref=f7e16]
      - generic [ref=f7e17]:
        - combobox "Search" [ref=f7e18]
        - button "Search" [ref=f7e19] [cursor=pointer]
      - list [ref=f7e24]:
        - listitem [ref=f7e25]: "Popular searches:"
        - listitem [ref=f7e26]:
          - link "featured" [ref=f7e27]:
            - /url: /search?q=featured&product=product
        - listitem [ref=f7e28]:
          - link "trendy" [ref=f7e29]:
            - /url: /search?q=trendy&product=product
        - listitem [ref=f7e30]:
          - link "sale" [ref=f7e31]:
            - /url: /search?q=sale&product=product
        - listitem [ref=f7e32]:
          - link "new" [ref=f7e33]:
            - /url: /search?q=new&product=product
      - status [ref=f7e34]
```