# Backlog - Future Tasks & Ideas

**Last Updated**: 2025-10-27

Items here are not prioritized for immediate work but may be valuable in the future.

---

## Features

### Advanced Preamble Management
- Preamble A/B testing framework
- Automated performance comparison
- Preamble recommendation engine (suggests best preamble based on page type/state)
- Visual preamble editor with preview

### Intelligent Project Setup Enhancements
- Multi-page crawling (beyond just homepage)
- Automatic sitemap detection
- Page type classification using computer vision
- Bulk URL import via CSV/sitemap

### Reporting & Analytics
- Executive dashboard (compliance scores over time)
- State compliance comparison
- Page type violation heatmap
- Cost analysis per project
- Automated compliance reports (PDF export)

### Notification System
- Email alerts for critical violations
- Slack/Teams integration
- Webhook support for custom integrations
- Scheduled compliance summaries

### Rule Management Enhancements
- Rule templates (common rules across states)
- Rule inheritance (parent-child rule relationships)
- Rule effectiveness tracking (which rules catch most violations)
- Suggested rule improvements based on check history

---

## Technical Improvements

### Database
- PostgreSQL migration (if SQLite becomes limiting)
- Full-text search for rules/legislation
- Database connection pooling optimization
- Read replicas for scaling

### Performance
- Redis caching layer
- Background job queue (Celery/RQ)
- CDN for screenshot delivery
- GraphQL API (alternative to REST)

### Security
- OAuth2 provider support (Google, Microsoft)
- Role-based access control (admin, reviewer, viewer)
- API rate limiting
- Audit logging for all operations

### DevOps
- CI/CD pipeline (GitHub Actions)
- Automated testing in pipeline
- Blue/green deployment
- Health monitoring (Prometheus/Grafana)
- Automated backups with rotation

### Code Quality
- Pre-commit hooks (Black, ESLint, Prettier)
- Dependency vulnerability scanning
- Code coverage requirements (>80%)
- API versioning strategy

---

## UI/UX Improvements

### Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation throughout
- Screen reader optimization
- High contrast mode

### User Experience
- Onboarding wizard for new users
- Interactive tutorial/tooltips
- Keyboard shortcuts
- Bulk operations (select multiple, batch approve)
- Drag-and-drop URL management

### Mobile
- Responsive design improvements
- Mobile-specific UI for compliance checks
- Push notifications for mobile users

---

## Integrations

### CMS Platforms
- WordPress plugin (monitor compliance from WP admin)
- Shopify app
- Dealer.com integration
- DealerSocket integration

### Marketing Tools
- Google Analytics integration (track compliance vs conversion)
- Tag Manager integration
- SEO impact analysis

### Legal/Compliance Tools
- Export to compliance management systems
- Integration with legal document management
- Automated regulatory update checking

---

## Research & Exploration

### AI/ML Enhancements
- Fine-tuned model for automotive compliance (vs general GPT)
- Custom embeddings for rule similarity
- Automated rule extraction from new regulations
- Predictive compliance (flag potential issues before violations)

### Alternative Approaches
- Browser extension for real-time compliance checking
- Static site analysis (pre-deployment checks)
- Compliance-as-code (infrastructure as code but for compliance)

---

## Won't Do (Parked Ideas)

### Multi-tenant SaaS
- Too complex for current needs
- Single-instance deployment sufficient
- Would require major architecture changes

### Real-time Monitoring
- Scheduled checks are adequate
- Real-time would increase costs significantly
- Could revisit if customer demand exists

### Mobile App (Native)
- Web app is sufficient
- Responsive design covers mobile use cases
- Maintenance overhead too high

---

## Moving Items

**From Backlog to TODO_NEW**:
- When item becomes prioritized
- Add to TODO_NEW.md with priority level
- Remove from this file or mark as "→ Moved to TODO_NEW"

**From TODO_NEW to Backlog**:
- When deprioritizing an item
- Add context for why it was deprioritized
- Consider if it's truly needed or just "nice to have"
