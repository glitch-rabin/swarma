# Agentic Storefront

## Mission

Optimize e-commerce for AI agent discovery and purchase. In 2026, AI agents (ChatGPT, Copilot, Gemini, Perplexity) are becoming the new storefront. Product data, descriptions, and structured metadata must be optimized for machines, not just humans. This squad systematically tests what makes AI agents recommend and convert.

## How This Actually Works in 2026

Shopify launched Agentic Storefronts (activating by default for all stores, late March 2026) and co-developed the Universal Commerce Protocol (UCP) with Google. UCP endorsed by Walmart, Target, Etsy, Amex, Mastercard, Stripe, Visa. This is live infrastructure.

AI-driven traffic to Shopify stores: 7x increase since Jan 2025. AI-attributed orders: 11x increase since Jan 2025. Early movers get disproportionate discovery.

The protocol stack: REST, MCP (Model Context Protocol), AP2 (Agent Payments Protocol), A2A (Agent2Agent). A `ucp.json` manifest acts as a machine-readable passport for your store.

## Experiment Patterns

1. **Product description optimization**: structured vs narrative descriptions -- measure AI-attributed conversion rate
2. **AI channel performance**: ChatGPT vs Copilot vs Gemini -- which drives higher-intent traffic
3. **Pricing display**: sale price vs original+discount vs "best value" framing in structured data
4. **Category targeting**: which product categories get recommended most by AI agents
5. **Review signal**: 100+ reviews vs 10 reviews -- measure AI recommendation frequency
6. **UCP early adoption**: compare AI-attributed revenue before/after UCP activation

## Metrics

- **Primary**: ai_attributed_conversion_rate
- **Discovery**: ai_agent_recommendation_frequency per product
- **Revenue**: ai_attributed_revenue, average_order_value_ai_vs_human
- **Channel**: traffic_and_conversion_by_ai_platform (ChatGPT, Copilot, Gemini)
- **Technical**: ucp_manifest_completeness, structured_data_coverage

## Constraints

- UCP manifest must be complete and valid (missing fields = invisible to AI agents)
- Product data must be machine-readable first, human-readable second
- Pricing must be real-time accurate (stale pricing = lost AI trust = lower recommendations)
- AI-optimized does not mean human-unfriendly. Both must work.
- Track AI-attributed revenue separately from organic (different optimization levers)
