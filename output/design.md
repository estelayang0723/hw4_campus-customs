# Campus Customs storefront design

## Color and hierarchy

The requested Yale Blue (`#0F4D92`) replaces the previous black/pink theme. It anchors the navigation, primary buttons, chat header, user chat bubbles, links, and accent text. Crisp white (`#FFFFFF`) is the main background and card surface. Soft grey sections (`#F6F8FA`, `#F3F5F7`) distinguish the hero, footer, and supporting areas without competing with merchandise. Dark slate body text and muted blue-grey secondary text keep descriptions readable. Out-of-stock badges retain a contrasting red treatment so availability is not confused with brand decoration.

A consistent blue navigation bar and clear call-to-action buttons create a recognizable collegiate identity and make the next action easier to find. This is an original student storefront treatment inspired by Yale's visual character, not a claim of university endorsement.

## Typography

Playfair Display, with a Georgia/serif fallback, styles page and section headings. Its traditional letterforms convey an established collegiate character. Inter, with Arial/sans-serif fallback, styles body copy, navigation, prices, product names, forms, and chat text for readable shopping details. Google Fonts supplies the web fonts; local fallbacks keep the site usable if the font request fails. Generous line spacing and responsive heading sizes preserve readability on small screens.

## Merchandise cards

The clean grid uses four columns on wide displays and two on smaller displays. White cards have 12px rounded corners, a light border, and a restrained shadow. Hover raises the card 4px, deepens the shadow over 250ms, and scales the product image to 1.05 over 350ms. Images remain contained in their frames. Product name, USD price, short description, availability badge, and detail-page link remain intact. Chat recommendations reuse the same component in a compact two-column grid.

The visual separation helps shoppers compare products, while subtle hover feedback makes clickability apparent. Authentic database images and prices remain the focus rather than decorative effects.

## Chat

The floating Yale Blue toggle now contains an original Bulldog icon drawn with HTML/CSS: folded ears, eyes, and a rounded muzzle. No image generation or official logo asset is used. The icon is decorative (`aria-hidden`) and the button retains its readable label and expanded state.

The chat panel has a blue header, rounded corners, and a soft shadow. User bubbles are Yale Blue with white text; assistant bubbles use light grey with dark text. Rounded bubble corners, generous spacing, and a blue typing indicator give the conversation a friendly, readable appearance. Saved-history notices, error feedback, product cards, and message input behavior are preserved.

## Motion and accessibility

A pathname-keyed content wrapper applies a 320ms fade-in and 6px upward transition on route navigation, including transitions between product details. Navigation and the chat widget remain outside the wrapper, so route animations do not reset the conversation. Hover and focus states make controls easier to recognize; keyboard outlines remain visible, with white outlines on the blue navbar.

`prefers-reduced-motion` disables page entrance animation, product zoom/lift, button lift, and the typing-dot animation. Motion provides feedback without being required to understand or operate the interface.

## Shopper and business value

The restrained blue/white palette, serif headings, consistent spacing, and clear product presentation aim to make the store feel coherent and trustworthy. Readable details and obvious actions reduce effort when browsing. The approachable chat icon invites questions, and consistent cards make it easy to move from recommendations into product details. These are design goals rather than measured conversion claims.

## Verification

The TypeScript check and Vite production build pass. Existing routes, product links, authentication, inventory badges, chat, and memory logic remain in place; this update changes presentation and adds the route transition wrapper.
