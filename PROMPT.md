Implement a complete SDD process PER BRANCH in the order specified below for performing the following changes. Remember to use engram to store the output of all of your process.
Dont push refs to main unless i tell you so.
BRANCH: main
1. Terraform format is returning status 3 
    Run terraform fmt -check -recursive infra/
    terraform fmt -check -recursive infra/
    shell: /usr/bin/bash -e {0}
    env:
        TERRAFORM_CLI_PATH: /home/runner/work/_temp/82d25845-0e98-4068-a745-64185730f081
    infra/modules/crud/main.tf
    Error: Terraform exited with code 3.
    Error: Process completed with exit code 1.

2. Look at this functionalities, there are still bugs
✅ Funcionales (14/16)
Herramienta	Estado	Detalle
product_create	✅ OK	Crea productos correctamente
product_read	✅ OK	Lee producto por ID
product_update	✅ OK	Actualiza nombre y precio
product_delete	✅ OK	Elimina producto
product_list	✅ OK	Lista todos los productos
product_search	✅ OK	Búsqueda por nombre funciona
dictionary_create	✅ OK	Crea entradas
dictionary_read	✅ OK	Lee entrada por palabra
dictionary_update	✅ OK	Actualiza definición
dictionary_delete	✅ OK	Elimina entrada
dictionary_list	✅ OK	Lista todas las entradas
shopping_cart_create	✅ OK	Crea carrito vacío
shopping_cart_read	✅ OK	Lee carrito
shopping_cart_update	✅ OK	Actualiza productos del carrito
shopping_cart_remove_product	✅ OK	Elimina producto del carrito
shopping_cart_delete	✅ OK	Elimina carrito
❌ Con bugs (2/16)
Herramienta	Estado	Bug
word_trick	❌ FAIL	Siempre devuelve api error
shopping_cart_add_product	❌ BUG	Devuelve carrito con productos vacíos []
shopping_cart_get_total	❌ BUG	Devuelve el carrito con productos vacíos en vez del total

3. Create swagger api for apigw api
BRANCH: ci/security
4. Use CodeQL and Dependabot from github for security
5. Use SonarQube 
BRANCH: feat/website-and-deployment
6. Create an application website using nextjs, tailwindcss and shadcnui for ui components using the api endpoints.
    main page: three buttons in the middle of the screen, minimalistic, white background and the buttons are outlined black.
    button 1: Days Dictionary below a book icon
    button 2: Says shopping below shopping cart icon
    button 3: Says word trick below letter icon
    Each button leads to a different path.
    Dictionary: Shows a list of definitions, Can store definitions, and lookup for definitions
    Shopping cart: Shows a list of products with their price (an let you create products in the upper part), and products have an icon of adding to cart, in the bottom there is a "Create cart button" and when clicked, it creates the cart and shows a modal with all the products, their price, and the total price (specify that it includes taxes)
    Word Trick: Single input, when click in word trick button on the right of the input, below it shows the output of the operation.
7. Deploy in amplify
BRANCH: feat/obervability
8. Create a cloudwatch dashboard in the terraform file.
    The dashboard should have the following metrics, MCP Calls, MCP Errors, API Calls, API Errors, Website Visitors, propose more meaningful metrics.