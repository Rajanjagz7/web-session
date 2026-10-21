# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — coupon code (CP-01..CP-10) >> CP-02 nonexistent coupon code shows an invalid-code message
- Location: tests\cart.spec.ts:140:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('body')
Expected pattern: /invalid|doesn.?t exist|not valid|not found/i
Received string:  "·····················
      Skip to content····································································
        Cart··································································································································
       You're only $990.95 away from FREE shipping··············
905·····················································································································
                          image··················································
                          Product··················································
                          Total··················································
                          Quantity··········································································································································································································································································································
                          Andis Clipper Oil 118ml·····························································
                                    $9.05·······························································································································································································································
                                    Decrease quantity for Andis Clipper Oil 118ml···················································································································································
                                    Increase quantity for Andis Clipper Oil 118ml··········································································································································································································································································································································································································································································································································································································································································································································································································
                Loading...·····················································································································
            Subtotal
            $9.05························
          Taxes and shipping calculated at checkout····················································
            Check out······················
            View Cart··································································································································································································································································································································
               What are you looking for ?··································
                Search························································································································································································································································································
          Popular searches:·················································
              featured··········································································
               trendy··········································································
               sale··········································································
               new···························································································································································································································································································································································································································································
          menu\"·················································································································
      CLIPPERS & ELECTRICALS············
      HAIR PRODUCTS············
      BARBER ESSENTIALS············
      BUNDLES & KITS···························································································
Log in·····························
 TW·············································································
FB················································································
IN·············································································
Snapchat·············································································
Vimeo·················································································································································································································
      CLIPPERS & ELECTRICALS······················································
      HAIR PRODUCTS······················································
      BARBER ESSENTIALS······················································
      BUNDLES & KITS···················································································································································································
                Wishlist····································
                    0·············································································
Cart11 item·········································
            Log in··············································································································································
        Sign In····························
          Email·············································
            Password······································
          Forgot your password?··················
          Sign Up··································
        Sign in···················································································
    Your Shopping Cart·········
    Home·······················
    Your Shopping Cart·······································
    Cart························
    Your cart is empty
    Browse our range and add your first product to get started.·····
      Continue shopping
    Have an account?·······
        Log in to check out faster.·······················
            Cart····························
                Product
                Total
                Quantity
                Total·······················································································································································································································································
                  Andis Clipper Oil 118ml
                        $9.05·······························································································································································································································································································································································································
                          $9.05············································································································
                        Quantity·······································································
                          Decrease quantity for Andis Clipper Oil 118ml···········································································································
                          Increase quantity for Andis Clipper Oil 118ml····························································································································································································································································································································································································································································································································································································································································································
                          $9.05···········································································································································
                             X········································································································································
    Loading...········
    Continue shopping··································································································
                    Subtotal·······································
                    $9.05 AUD·······················································
                Taxes and shipping calculated at checkout·················································································································································
  Apply···························································
            Check out·································································································································
                    Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.······················································································································································································
                        Your email address·······················
                      Subscribe·············································································
                 Useful links·················································
                            Clippers & Electricals···············································································
                            Hair Products···············································································
                            Barber Essentials···············································································
                            Bundles & Kits···············································································
                            Trade Portal···························
                        Help & Support·················································
                            About Us···············································································
                            Contact···············································································
                            FAQ···············································································
                            Shipping···························
                        Resources·················································
                            Returns···············································································
                            Privacy···············································································
                            Terms & Conditions···············································································
                            Warranty·······································································································································
 TW·································································
FB····································································
IN·································································
Snapchat·································································
Vimeo···················································································································
            Payment methods·············
                  American Express··················
                  Apple Pay··················
                  Google Pay··················
                  Mastercard··················
                  PayPal·················
                  Union Pay·················
                  Visa·························································
           © 2026 ZeroGap Supply Co.···················································
      Choosing a selection results in a full page refresh.·············································································································
		To top·················································
You will not be allowed to compare more than 4 products at a time
View compare····················································································
     Home····························
  Shop··························································································································································································
                Wishlist···················································
               Log in···························································································································································
"

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for locator('body')
    11 × locator resolved to <body id="your-shopping-cart" class="gradient template-cart page-type__your-shopping-cart">…</body>
       - unexpected value "
    
     
    
    
      Skip to content
    
     
   
     
    
    
     
    





    
  
  
    
    
        Cart
        
          

  
  
  
  
  
  
  
  
  
 
         
        
      
      
        
          
            


  
  
  
  
       You're only $990.95 away from FREE shipping
      
  




905
   






 
                
                  
                    
                      
                        
                          image
                        
                        
                          Product
                        
                        
                          Total
                        
                        
                          Quantity
                        
                      
                    

                    
                          
                            
                              
                               
                              
                            
                          

                          Andis Clipper Oil 118ml

                            
                              
                                    $9.05
                                  
                            
                              
                            
                              
                                
                                  
                                    Decrease quantity for Andis Clipper Oil 118ml
                                    
  


                                  
                                  
                                  
                                    Increase quantity for Andis Clipper Oil 118ml
                                    
  


                                  
                                
                              

                              
                                
                                
                                  
                                  
                                  
                                  
                                
                              
                              
                                
                                  

  
  
  
  
  
  
  
  
  
 
         
                                
                              
                            
                          
                        
                  
                
              
                Loading...
              
            
            
          
        

      
        
        
        

        
          
            Subtotal
            $9.05
          

          

          Taxes and shipping calculated at checkout

        

        

        
          
          
            Check out
          
          
            View Cart
          
        
      
    
  





   
    


   
    





  
  
  
  
  
  
  





 
 
          
            
            
            
             
                 
            
            
            
            
            
            
            
            
            
            
              
               What are you looking for ?  
              
                
                Search
                
                
                  
                    
                  
                
                
                  
                  
                  
                  
                
              
                
         
        
        
          Popular searches:
          
          
                          
              featured
            
           
          
          
                          
               trendy
            
           
          
          
                          
               sale
            
           
          
          
                          
               new
            
           
          
        
        
        


   
                  
                    
                      
                    
                  
                

                
    
              
                  
                  




   




 
  
    
  

  
    
  
 



  
   
    
            
        
          
            
              
  

       
            
          
               
          
          menu"
          

  
  
  
  
  
  
  
  
  
 
         
          
            
              
                 





      CLIPPERS & ELECTRICALS
    







      HAIR PRODUCTS
    







      BARBER ESSENTIALS
    







      BUNDLES & KITS
    


               
              
            
             
                      



Log in
                        




 TW
                        
                      
                        




FB
                        
                      
                        
  
  

IN
                        
                      
                        
  

Snapchat
                        
                      
                        
  

Vimeo
                        
                      
                
          
        
      
        
            
      
                
                
                    






   

  
      
      
    
      CLIPPERS & ELECTRICALS
    
    
  

  










   

  
      
      
    
      HAIR PRODUCTS
    
    
  

  










   

  
      
      
    
      BARBER ESSENTIALS
    
    
  

  










   

  
      
      
    
      BUNDLES & KITS
    
    
  

  





                  
               
        
        




               
  
    
  
      
        
                 
              
                 
   
 
                Wishlist
                
                  
                    0
                  
                
              
 
























Cart11 item
          
       
       



          
            Log in              
          
        

        
    
  
 
  




   
     

   
    
     
    
      
      
        
          
        
      
        Sign In
  
    
        
          
          Email
        
        
      
         
         
            Password
          
          
        
      
          Forgot your password?
        
        
          Sign Up
        
                
       
        Sign in
        
    


              
  
      
      

 
  
   
 
    
      
          
    Your Shopping Cart
        
    Home

    
   
       
    
    Your Shopping Cart
    

    
 
   

 

        






  
    Cart
  

  
    
      
    
    Your cart is empty
    Browse our range and add your first product to get started.
    
      Continue shopping
    Have an account?
      
        Log in to check out faster.
      

  
    
      
            Cart
            
              
                Product
                Total
                Quantity
                Total
              
            

            
                  
                    
                      
                       
                        
                          
                        
                    
                  

                  Andis Clipper Oil 118ml
                        $9.05
                      

                      
                  

                  
                    
                      
                         
                          
                          
                          
                          
                          
                          
                      
                    
                    
                          $9.05
                        
                  

                  
                    
                      
                        Quantity
                      
                      
                        
                          Decrease quantity for Andis Clipper Oil 118ml
                          
  


                        
                        
                        
                          Increase quantity for Andis Clipper Oil 118ml
                          
  


                        
                      
                   
                    
                    
                      
                      
                        
                        
                        
                        
                      
                    
                  

                  
                    
                      
                        
                          
                          
                          
                          
                          
                          
                      
                    

                    
                          $9.05
                        
                  
                  
                    
                         
                            
                             X
                            
                           
                    
                  
                
          
    

    
    Loading...
  
    
    Continue shopping
                          








  
    
      

        


                
                  
                    Subtotal
                  

                  
                    $9.05 AUD
                  
                

                

                Taxes and shipping calculated at checkout


              


        
        

        
        
          


  
    
      
      

  
  
  
  
  
  
  
  
  
 
         
    
  
  
  
  Apply
  




        

        
        

          

          
            Check out
          

        

      
    
  




      
     
   













      
    
                      
                      
                    Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
                  

                  
                
                    
                  
                  
                    
                      
                      
                        Your email address
                      
                      Subscribe
                      
                                    
                
                 Useful links
                





                          
                            Clippers & Electricals
                          
                        
                          
                            Hair Products
                          
                        
                          
                            Barber Essentials
                          
                        
                          
                            Bundles & Kits
                          
                        
                          
                            Trade Portal
                          
                        Help & Support
                





                          
                            About Us
                          
                        
                          
                            Contact
                          
                        
                          
                            FAQ
                          
                        
                          
                            Shipping
                          
                        Resources
                





                          
                            Returns
                          
                        
                          
                            Privacy
                          
                        
                          
                            Terms & Conditions
                          
                        
                          
                            Warranty
                          
                        
                  
                
                     
                    




 TW
                    
                  
                    




FB
                    
                  
                    
  
  

IN
                    
                  
                    
  

Snapchat
                    
                  
                    
  

Vimeo
                    
                        
                
                  
          
    
         
      
            Payment methods
            
                  American Express

                
                  Apple Pay

                
                  Google Pay

                
                  Mastercard

                
                  PayPal
                
                  Union Pay
                
                  Visa

                
          
                  
        
           © 2026 ZeroGap Supply Co.
        
          
      
      
    
  


 
    
      Choosing a selection results in a full page refresh.
    

    
         
                
        
      
    








      
      
    

  
  

  


 
    
  
		To top
	     

 


 

      






    



    
      

You will not be allowed to compare more than 4 products at a time
View compare
 

  
  
  
  
  
  
  
  
  
 
          
   
  
     
  
    
   
   
   
   
   
     Home
   
   
  
  
  
  
  
    
  Shop
   
  
  
                
               
                
               

                
                  
                    
                  
                
               
                Wishlist
              

              
                



               Log in
              
               
   

          
    
      

  
  
  
  
  
  
  
  
  
 
           
      
        
          
        
      
    
  



"
  - Protocol error (Runtime.callFunctionOn): Internal server error, session closed.

```

```yaml
- banner:
  - group:
    - button "Menu"
  - heading "ZeroGap Supply Co" [level=1]:
    - link "ZeroGap Supply Co":
      - /url: /
      - img "ZeroGap Supply Co"
  - img
  - link:
    - /url: /pages/wishlist
    - img
  - button "1 item":
    - img
    - text: 1 item
- main:
  - navigation "breadcrumbs cart":
    - heading "Your Shopping Cart" [level=2]
  - heading "Cart" [level=1]
  - table "Cart":
    - caption: Cart
    - rowgroup:
      - row "Andis Clipper Oil 118ml Andis Clipper Oil 118ml $9.05 Quantity Decrease quantity for Andis Clipper Oil 118ml 1 Increase quantity for Andis Clipper Oil 118ml Remove Andis Clipper Oil 118ml":
        - cell "Andis Clipper Oil 118ml":
          - img "Andis Clipper Oil 118ml"
        - cell "Andis Clipper Oil 118ml $9.05":
          - link "Andis Clipper Oil 118ml":
            - /url: /products/andis-clipper-oil-118ml?variant=45211104084037
          - text: $9.05
        - cell "Quantity Decrease quantity for Andis Clipper Oil 118ml 1 Increase quantity for Andis Clipper Oil 118ml":
          - text: Quantity
          - button "Decrease quantity for Andis Clipper Oil 118ml"
          - spinbutton "Quantity for Andis Clipper Oil 118ml": "1"
          - button "Increase quantity for Andis Clipper Oil 118ml"
          - alert
        - cell "Remove Andis Clipper Oil 118ml":
          - link "Remove Andis Clipper Oil 118ml":
            - /url: /cart/change?id=45211104084037:52a38e27dde3abfa19d6dcee03b277c3&quantity=0
            - text: X
  - link "Continue shopping":
    - /url: /collections/all
  - heading "Subtotal" [level=2]
  - paragraph: $9.05 AUD
  - text: Taxes and shipping calculated at checkout
  - textbox "Enter Your Discount Code": FAKECODE99
  - button "Apply"
  - button "Check out"
- contentinfo:
  - link:
    - /url: /
  - paragraph: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
  - textbox "Your email address"
  - button "Subscribe"
  - heading "Useful links" [level=2]
  - img
  - heading "Help & Support" [level=2]
  - img
  - heading "Resources" [level=2]
  - img
  - list:
    - listitem:
      - link "TW":
        - /url: "#"
        - img
        - text: TW
    - listitem:
      - link "FB":
        - /url: "#"
        - img
        - text: FB
    - listitem:
      - link "IN":
        - /url: "#"
    - listitem:
      - link "Snapchat":
        - /url: "#"
    - listitem:
      - link "Vimeo":
        - /url: "#"
  - text: Payment methods
  - list:
    - listitem:
      - img "American Express"
    - listitem:
      - img "Apple Pay"
    - listitem:
      - img "Google Pay"
    - listitem:
      - img "Mastercard"
    - listitem:
      - img "PayPal"
    - listitem:
      - img "Union Pay"
    - listitem:
      - img "Visa"
  - paragraph: © 2026 ZeroGap Supply Co.
- link "To top":
  - /url: "#your-shopping-cart"
  - img
  - text: To top
- link "Home":
  - /url: /
  - img
  - text: Home
- link "Shop":
  - /url: /collections
  - img
  - text: Shop
- link "Wishlist":
  - /url: /pages/wishlist
  - img
  - text: Wishlist
- link "Log in":
  - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgxMDE1LCJuYmYiOjE3OTI1NzYyMTV9.OirwQUBG-Qr9NosWE3VnF3wJ6D8LNj5X-czqd0DSYgA
  - img
  - text: Log in
```

# Test source

```ts
  51  |     expect(Number(value)).toBeGreaterThanOrEqual(0);
  52  |   });
  53  | 
  54  |   test('UC-05 rapid successive quantity changes settle on a correct final value', async ({ unlockedPage: page }) => {
  55  |     await addFirstProductToCart(page);
  56  |     await page.goto('/cart');
  57  |     const plusButton = page.locator('button[name="plus"], [class*="quantity"] button:has-text("+")').first();
  58  |     if (!(await plusButton.isVisible().catch(() => false))) {
  59  |       test.skip(true, 'No +/- quantity stepper on the cart page for this theme.');
  60  |       return;
  61  |     }
  62  |     for (let i = 0; i < 5; i++) await plusButton.click({ timeout: 1000 }).catch(() => {});
  63  |     await page.waitForTimeout(1000);
  64  |     const qty = quantityInput(page).first();
  65  |     const value = await qty.inputValue().catch(() => '');
  66  |     expect(Number(value)).toBeGreaterThan(1);
  67  |   });
  68  | });
  69  | 
  70  | test.describe('Cart page — remove items (RC-01..RC-02)', () => {
  71  |   test('RC-01 removing the last item shows the empty-cart state', async ({ unlockedPage: page }) => {
  72  |     await addFirstProductToCart(page);
  73  |     await page.goto('/cart');
  74  |     const removeButton = page.locator('[class*="remove"], a[href*="quantity=0"], button[aria-label*="remove" i]').first();
  75  |     if (!(await removeButton.isVisible().catch(() => false))) {
  76  |       test.skip(true, 'No remove control found on the cart page for this theme.');
  77  |       return;
  78  |     }
  79  |     await removeButton.click();
  80  |     await page.waitForTimeout(800);
  81  |     await expect(page.locator('body')).toContainText(/empty|nothing in your cart/i);
  82  |   });
  83  | 
  84  |   test('RC-02 double-clicking remove does not throw an error', async ({ unlockedPage: page }) => {
  85  |     await addFirstProductToCart(page);
  86  |     await page.goto('/cart');
  87  |     const removeButton = page.locator('[class*="remove"], a[href*="quantity=0"], button[aria-label*="remove" i]').first();
  88  |     if (!(await removeButton.isVisible().catch(() => false))) {
  89  |       test.skip(true, 'No remove control found on the cart page for this theme.');
  90  |       return;
  91  |     }
  92  |     const errors: string[] = [];
  93  |     page.on('pageerror', (e) => errors.push(e.message));
  94  |     await removeButton.click().catch(() => {});
  95  |     await removeButton.click({ timeout: 1000 }).catch(() => {});
  96  |     await page.waitForTimeout(500);
  97  |     expect(errors).toHaveLength(0);
  98  |   });
  99  | });
  100 | 
  101 | test.describe('Cart page — subtotal (ST-01..ST-04)', () => {
  102 |   test('ST-01 subtotal updates immediately after a quantity change', async ({ unlockedPage: page }) => {
  103 |     await addFirstProductToCart(page);
  104 |     await page.goto('/cart');
  105 |     const subtotal = page.locator('[class*="subtotal"], [class*="total"]').first();
  106 |     const before = (await subtotal.textContent().catch(() => '')) || '';
  107 |     const qty = quantityInput(page).first();
  108 |     if (!(await qty.isVisible().catch(() => false))) {
  109 |       test.skip(true, 'No editable quantity input on the cart page for this theme.');
  110 |       return;
  111 |     }
  112 |     await qty.fill('2');
  113 |     await qty.press('Enter').catch(() => {});
  114 |     await page.waitForTimeout(1000);
  115 |     const after = (await subtotal.textContent().catch(() => '')) || '';
  116 |     expect(after).not.toBe(before);
  117 |   });
  118 | 
  119 |   test('ST-03 subtotal on an empty cart shows $0.00, never NaN', async ({ unlockedPage: page }) => {
  120 |     await page.goto('/cart');
  121 |     await expect(page.locator('body')).not.toContainText(/NaN|undefined/i);
  122 |   });
  123 | });
  124 | 
  125 | test.describe('Cart page — coupon code (CP-01..CP-10)', () => {
  126 |   test('CP-01 empty coupon field submit does not error', async ({ unlockedPage: page }) => {
  127 |     await addFirstProductToCart(page);
  128 |     await page.goto('/cart');
  129 |     const input = couponInput(page);
  130 |     if (!(await input.isVisible().catch(() => false))) {
  131 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  132 |       return;
  133 |     }
  134 |     await input.fill('');
  135 |     await input.press('Enter');
  136 |     await page.waitForTimeout(500);
  137 |     await expect(page.locator('body')).not.toContainText(/500|internal server error/i);
  138 |   });
  139 | 
  140 |   test('CP-02 nonexistent coupon code shows an invalid-code message', async ({ unlockedPage: page }) => {
  141 |     await addFirstProductToCart(page);
  142 |     await page.goto('/cart');
  143 |     const input = couponInput(page);
  144 |     if (!(await input.isVisible().catch(() => false))) {
  145 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  146 |       return;
  147 |     }
  148 |     await input.fill('FAKECODE99');
  149 |     await input.press('Enter');
  150 |     await page.waitForTimeout(1000);
> 151 |     await expect(page.locator('body')).toContainText(/invalid|doesn.?t exist|not valid|not found/i);
      |                                        ^ Error: expect(locator).toContainText(expected) failed
  152 |   });
  153 | 
  154 |   test('CP-06 applying the same coupon twice does not double-discount', async ({ unlockedPage: page }) => {
  155 |     if (!process.env.VALID_COUPON) {
  156 |       test.skip(true, 'Set VALID_COUPON=<real code> to run this check.');
  157 |       return;
  158 |     }
  159 |     await addFirstProductToCart(page);
  160 |     await page.goto('/cart');
  161 |     const input = couponInput(page);
  162 |     if (!(await input.isVisible().catch(() => false))) {
  163 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  164 |       return;
  165 |     }
  166 |     await input.fill(process.env.VALID_COUPON!);
  167 |     await input.press('Enter');
  168 |     await page.waitForTimeout(1000);
  169 |     const subtotalAfterFirst = await page.locator('[class*="total"]').first().textContent();
  170 |     await input.fill(process.env.VALID_COUPON!);
  171 |     await input.press('Enter');
  172 |     await page.waitForTimeout(1000);
  173 |     const subtotalAfterSecond = await page.locator('[class*="total"]').first().textContent();
  174 |     expect(subtotalAfterSecond).toBe(subtotalAfterFirst);
  175 |   });
  176 | 
  177 |   test('CP-08 coupon code with leading/trailing spaces is trimmed and accepted', async ({ unlockedPage: page }) => {
  178 |     if (!process.env.VALID_COUPON) {
  179 |       test.skip(true, 'Set VALID_COUPON=<real code> to run this check.');
  180 |       return;
  181 |     }
  182 |     await addFirstProductToCart(page);
  183 |     await page.goto('/cart');
  184 |     const input = couponInput(page);
  185 |     if (!(await input.isVisible().catch(() => false))) {
  186 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  187 |       return;
  188 |     }
  189 |     await input.fill(`  ${process.env.VALID_COUPON}  `);
  190 |     await input.press('Enter');
  191 |     await page.waitForTimeout(1000);
  192 |     await expect(page.locator('body')).not.toContainText(/invalid|doesn.?t exist/i);
  193 |   });
  194 | 
  195 |   test('CP-09 injection-style coupon string is rejected, not reflected', async ({ unlockedPage: page }) => {
  196 |     await addFirstProductToCart(page);
  197 |     await page.goto('/cart');
  198 |     const input = couponInput(page);
  199 |     if (!(await input.isVisible().catch(() => false))) {
  200 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  201 |       return;
  202 |     }
  203 |     await input.fill('<script>alert(1)</script>');
  204 |     await input.press('Enter');
  205 |     await page.waitForTimeout(1000);
  206 |     const bodyHtml = await page.locator('body').innerHTML();
  207 |     expect(bodyHtml).not.toContain('<script>alert(1)</script>');
  208 |   });
  209 | 
  210 |   test('CP-10 a discount larger than the subtotal floors the total at $0.00', async ({ unlockedPage: page }) => {
  211 |     if (!process.env.OVERSIZED_COUPON) {
  212 |       test.skip(true, 'Set OVERSIZED_COUPON=<real code worth more than the cart total> to run this check.');
  213 |       return;
  214 |     }
  215 |     await addFirstProductToCart(page);
  216 |     await page.goto('/cart');
  217 |     const input = couponInput(page);
  218 |     if (!(await input.isVisible().catch(() => false))) {
  219 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  220 |       return;
  221 |     }
  222 |     await input.fill(process.env.OVERSIZED_COUPON!);
  223 |     await input.press('Enter');
  224 |     await page.waitForTimeout(1000);
  225 |     await expect(page.locator('body')).not.toContainText(/-\$|−\$/); // no negative total
  226 |   });
  227 | });
  228 | 
```