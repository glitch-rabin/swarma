# Agentic Storefront Strategy

## Seed Knowledge (pre-experiment baseline)

Data from 2026 growth ops landscape research. Agentic commerce is the newest channel -- most e-commerce operators haven't optimized for it. First-mover advantage is real.

### The Infrastructure (2026)

Shopify Agentic Storefronts: activating by default for all stores, late March 2026.
- Enable in Shopify admin: Settings -> Apps and sales channels
- Toggle specific AI channels: ChatGPT, Copilot, Gemini
- Shopify Catalog auto-syndicates product data to all enabled AI platforms
- One setup, everywhere

Universal Commerce Protocol (UCP): co-developed by Shopify + Google.
- `ucp.json` manifest = machine-readable store passport
- Broadcasts product catalog, pricing, inventory, shipping to any compliant AI agent
- Protocol stack: REST, MCP, AP2 (Agent Payments Protocol), A2A (Agent2Agent)
- Checkout via OAuth 2.0 (user's saved shipping/payment info)

Endorsed by: Walmart, Target, Etsy, American Express, Mastercard, Stripe, Visa. This is not speculation -- it's live infrastructure.

### Traffic & Revenue Data

| Metric | Trend | Timeframe |
|--------|-------|-----------|
| AI-driven traffic to Shopify stores | **7x increase** | Since Jan 2025 |
| AI-attributed orders | **11x increase** | Since Jan 2025 |
| Compounding effect | Early movers get disproportionate discovery | Ongoing |

These numbers are compounding. The stores that optimize for AI agent discovery now will build a lead that's hard to close.

### Dynamic Pricing for AI Agents

AI agents compare prices across merchants in real-time. Pricing strategy shifts:
- **Real-time accuracy**: stale prices = AI agent stops recommending you
- **Competitive positioning**: AI agents surface "best value" -- price must be competitive within category
- **Transparent pricing**: AI agents can read and compare total cost (price + shipping + tax). Hidden fees = lower recommendation score.
- **Dynamic discounts**: time-limited offers may trigger AI agents to prioritize your product ("this deal expires in 2 hours")

### AI Product Recommendations

What makes AI agents recommend a product:
1. **Structured data completeness**: every field filled (title, description, price, images, specs, reviews, inventory)
2. **Review volume and quality**: 100+ reviews with 4+ stars = significant recommendation boost
3. **Description specificity**: "wireless earbuds with 30-hour battery, ANC, IPX5" > "great wireless earbuds"
4. **Image quality and variety**: multiple angles, lifestyle shots, size comparison
5. **Inventory status**: in-stock products always preferred over backorder
6. **Shipping speed**: faster shipping = higher recommendation priority

### Conversational Commerce Patterns

AI agents interact conversationally with shoppers:
- "Find me wireless earbuds under $80 with ANC"
- "Compare these two products"
- "What's the return policy?"
- "Apply this coupon code"
- "Ship to my saved address"

Product data must answer these queries directly. Structured specs > marketing prose. FAQ coverage of common purchase questions increases conversion.

### Shopify UCP Setup

1. Enable Agentic Storefronts (Settings -> Apps and sales channels)
2. Toggle on AI channels (ChatGPT, Copilot, Gemini)
3. Enable UCP to generate `ucp.json` manifest
4. Ensure product catalog is complete (no missing fields)
5. Verify pricing is real-time (not cached/stale)
6. Add structured data (product schema, FAQ schema, review schema)
7. Monitor AI-attributed traffic and orders separately

Non-Shopify stores: Shopify Agentic Plan -- use Shopify's catalog infrastructure without a full Shopify store.

### Patterns to Test

- [ ] Product descriptions: structured specs vs narrative vs hybrid -- AI recommendation rate
- [ ] AI channel comparison: ChatGPT vs Copilot vs Gemini -- conversion rate per channel
- [ ] Pricing display: sale price vs original+discount vs "best value" -- AI conversion
- [ ] Review threshold: impact of review count on AI recommendation frequency
- [ ] UCP activation: before/after AI-attributed revenue comparison
- [ ] Image count: 3 images vs 6 vs 10+ -- AI recommendation and conversion impact

### Anti-Patterns

- Marketing prose instead of structured specs (AI agents parse data, not vibes)
- Missing product fields (incomplete data = invisible to AI agents)
- Stale pricing (even 24-hour lag = lost recommendations)
- No AI-attributed revenue tracking (can't optimize what you can't measure)
- Ignoring UCP manifest validation (broken manifest = completely invisible)
- Same optimization for AI and human visitors (different discovery patterns, different needs)
