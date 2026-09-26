## Problem 1: Vibe coder prompts

create an AI_prompts.md file for me to log my prompts for this assignment. it needs a section for each problem. each section should include the problem name, my initial prompt, and any follow up prompts explaining what was missing. please log this current chat under problem 1.

## Problem 2: Analyze the database


i need to analyze the database for the shop. please look at the catalogue, inventory, and users tables in data/campus_customs.db. then, start a new file called output/harness.md. in that file, list each table, its fields, and write one short sentence for each field explaining why it matters for the storefront or the chatbot.

## Problem 3: Build the Campus Customs website

scaffold a react + vite + typescript frontend for campus customs. put a nav bar at the top linking to home, products, about us, log in, and create account.

for the home page, use this exact text:
Headline: Welcome to Campus Customs
Subheadline: Wear Your True Blue Pride.
Body: Gear up and show your spirit! Whether you're cheering on the Bulldogs at the Yale Bowl, heading to class, or representing from across the globe, Campus Customs is your ultimate destination for premium campus apparel. Dive into our exclusive collections and find the perfect gear to let your Bulldog pride shine in classic Yale Blue.

for the about us page, use this exact text:
Headline: Our Story: Rooted in Bulldog Spirit
Body: Born in the heart of New Haven, Campus Customs is more than just a merchandise store—it's a celebration of tradition, community, and the unmistakable Bulldog spirit. We know that wearing Yale Blue isn't just a color choice; it's a statement of pride. Our mission is to provide students, alumni, and passionate fans with high-quality, stylish, and comfortable gear. From classic tees to cozy winter hoodies, every item we curate is designed to help you carry a piece of campus with you wherever you go. Go Bulldogs!

on the products page, show product images with name, price, and description. make each product open a single-item page with full details. add a floating chat interface stub in the bottom right. also set up a simple fastapi app in backend/main.py to serve products and images.

## Problem 4: Create account and login


build a normal create account and login flow for the site. for creating an account, ask for first name, last name, email, password, and a confirm password field. for logging in, use email and password. save new accounts to the users table in the database, and make sure passwords are encrypted and stored securely so they cannot be accessed by hackers. make sure i can log in with the seed user (test@campuscustoms.yale.edu / password) and any new accounts i create. also, update the output/harness.md file to explain how this auth flow works, specifically what we store for a user and how passwords are protected.

## Problem 5: PydanticAI agent backend


set up the pydanticAI agent backend behind fastapi to power the chat widget. create the following files in the backend folder: prompts/prompt.md for the system prompt (include some basic campus customs voice and safety rules), agent.py for the agent wiring, tools.py for future tools, and models.py for pydantic types like chat replies. update main.py to expose a chat route so messages from the frontend get a reply from the agent. also, please update output/harness.md to explain how the frontend communicates with fastapi and how the agent is loaded with its prompt and model. make sure it runs via uvicorn main:app --reload --port 8000.

## Problem 6: Tools: product info and stock


create tools for the agent to look up real product information from campus_customs.db. the agent needs to be able to find a product's description, price, and check how many are in stock, specifically by size if the customer asks. the agent must only use real data from the database and should never make up prices or quantities. if a size is out of stock, it needs to state that clearly. update the prompts/prompt.md file so the agent knows when to use these tools for price and stock questions. also, update models.py with the necessary return types. finally, in output/harness.md, list each tool you created and explain the model fields chosen for the lookup results and why they were chosen.

## Problem 7: Chat search that updates the page


add a feature where if a customer asks the chat about specific items, like "what hoodies do you have?", the agent searches the catalogue and returns structured product matches. the frontend should then dynamically display these matching items as product cards with their image, name, price, and short info. make sure these dynamically loaded cards work just like the ones from problem 3—when clicked, they must open the single-item detail page. finally, update both prompts/prompt.md and output/harness.md to clearly explain the api contract, specifically how the search results are returned by the agent and rendered on the page.

## Problem 8: Customer memory


implement customer memory for the chat. if a user is logged in, save their chat history in the database and reload it when they return. guests can still chat, but we don't need to save their history. also, make sure the agent knows who is chatting by passing the user's name and email into the agent dependencies. additionally, pass the current page context to the agent so that if someone is on a product page and asks "do you have this in pink?", the agent knows exactly which item they are looking at. finally, document in output/harness.md how the chat history is stored, what customer fields the agent can see, and how the page context is passed to the agent.

## Problem 9: Usability improvements


now that the core shop works, let's implement some usability improvements. i need 2 frontend improvements that make the site look better and easier to use: first, add a 'typing...' loading indicator in the chat widget so users know the agent is thinking; second, add clear 'Out of Stock' visual badges on the product cards if the inventory is zero. i also need 2 backend/agent improvements to make the agent better, safer, or faster: first, create a new tool for the agent to suggest related or complementary items; second, implement chat history truncation (context window management) for the agent to keep it running fast and cheap on long conversations. implement these 4 specific features. also, create and write into a new file called output/usability.md. in this file, for each of the 4 improvements, detail exactly what was added and explain why it helps either a campus customs shopper or the business itself. ensure all improvements are actually working in the app.

## Problem 10: Style the website


please completely style the website so it looks like a premium, authentic Yale Campus Customs storefront. here are the specific design requirements:

Color Palette: use Yale Blue (#0F4D92) as the primary brand color for the navbar, buttons, and chat header. use crisp white for backgrounds and soft light grey for secondary sections.

Typography: use a classic, elegant serif font (like Playfair Display or Merriweather) for all page headers to give it that traditional Ivy League feel, and a clean sans-serif (like Inter or Roboto) for body text and product details for modern readability.

Product Presentation: display merchandise in a clean grid. give the product cards subtle rounded corners, a soft drop shadow, and a smooth hover animation where the product image slightly scales up (e.g., scale 1.05) and the shadow deepens.

Chat Widget: style it to be friendly and polished. use a Bulldog icon for the chat toggle button. inside the chat, use rounded, modern chat bubbles (Yale Blue for user, light grey for agent).

Motion: add soft fade-in transitions when navigating between pages.
after styling, create output/design.md. in that file, detail these specific font, color, and animation choices, and explain how this premium collegiate aesthetic builds brand trust and encourages customers to explore and buy.

## Problem 11: Site testing (app check)

i need to test the live site and document the results in a new file called output/app_check.html. please set up the basic html structure for this file. the page needs to include three specific test cases, each with a heading, an image tag using a relative path to the output/app_check_images/ folder, and a one or two sentence caption explaining what the screenshot proves. the three test cases are: 1. the chat checking the inventory level and giving honest stock/price from the database. 2. the dynamic search-result cards appearing after a category question like "what hoodies do you have?". 3. the "Out of Stock" visual badge usability feature i added earlier. i will take the actual screenshots myself and save them in the app_check_images folder, so just put placeholder image names like inventory.png, dynamic_cards.png, and usability.png in the html.

## Problem 12: Audit trail, safety, finish harness

please implement a logging mechanism that writes an append-only audit trail to a file named output/audit_trail.json. this log should record the agent-loop activity, specifically: the timestamp, tool name used, short args/result, and the stop reason. make sure this file is never wiped between runs. next, brainstorm some strict safety and operational rules for the agent (e.g. do not discuss sensitive topics, do not invent prices, keep responses concise) and add these directly into prompts/prompt.md. finally, completely fill out the output/harness.md file so it clearly explains how the system works. it must include: 1) the model fields in models.py and why they were chosen, 2) the tools and abilities of the agent, 3) the new safety rules, and 4) technical specs like loop limits, result caps, the AI models used, and exact commands on how to run both the frontend and backend.

## Problem 13: Push to GitHub and submit the URL


i am preparing to push my code to a public github repository for the final homework submission. please help me finalize the repository structure according to the problem 13 requirements:

create a .env.example file with placeholder values only.

update the .gitignore file to strictly ensure .env, data/campus_customs.db, and the data/products/ folder are ignored and not tracked by git.

update README.md to clearly explain how a grader can run both the frontend and backend after they place the local data pack.
please double-check that the file layout exactly matches the expected structure, ensuring everything is ready for a clean commit.