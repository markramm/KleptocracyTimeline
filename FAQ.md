# Frequently Asked Questions (FAQ)

## 🎯 About the Project

### What is the Kleptocracy Timeline?
The Kleptocracy Timeline is an open-source intelligence project documenting the systematic capture of democratic institutions from 1970 to 2025. It tracks 395+ verified events showing how democratic norms have been eroded through coordinated efforts across multiple domains.

### Why was this created?
To make invisible patterns visible. By documenting and connecting events across decades, we can see the systematic nature of democratic erosion that might otherwise appear as isolated incidents. This is intelligence infrastructure for democratic defense.

### Who created this?
This project was initiated by Mark Ramm and developed with the help of AI assistants to accelerate pattern recognition and analysis. It's now a community-driven effort welcoming contributions from anyone committed to factual documentation.

### Is this project partisan?
No. The timeline documents actions and their consequences regardless of political party. We focus on verifiable events, not partisan narratives. The data shows patterns of institutional capture that transcend party lines.

## 📊 About the Data

### How many events are documented?
Currently 395+ events spanning from 1970 to 2025, with exponential acceleration in recent years (162x increase from the 1970s to 2025).

### What are the "9 Capture Lanes"?
Through pattern analysis, we identified nine systematic methods of democratic erosion:
1. **Judicial Capture & Corruption** - Control of courts
2. **Electoral Manipulation & Voter Suppression** - Undermining voting
3. **Media Capture & Propaganda** - Information control
4. **Regulatory Capture & Dismantling** - Weakening oversight
5. **Financial Corruption & Money Laundering** - Illicit finance
6. **Executive Power Expansion** - Authoritarian consolidation
7. **Legislative Dysfunction & Capture** - Breaking governance
8. **Intelligence & Security Abuse** - Surveillance and control
9. **Social Division & Violence** - Fragmenting society

### How are events verified?
Every event requires:
- Minimum 2 credible sources
- Verification of claims against sources
- Archive creation for source preservation
- Cross-reference checking for consistency
- Community validation

### What does "importance" rating mean?
Events are rated 1-10 based on:
- Systemic impact on democratic institutions
- Number of people affected
- Precedent-setting nature
- Acceleration of capture patterns
- Long-term consequences

### Why do some events show as "predicted"?
Events scheduled for future dates are marked "predicted" until they occur and can be verified. These are based on announced plans, scheduled votes, or documented intentions.

## 🔧 Technical Questions

### What technology powers this?
- **Data**: YAML files with rigorous schema validation
- **Frontend**: React.js with static JSON data
- **Hosting**: GitHub Pages (no backend required)
- **Visualization**: D3.js for network graphs
- **Version Control**: Git/GitHub for collaboration

### Can I download the data?
Yes! All data is open source:
- **Full timeline**: `/timeline_complete.json`
- **Individual events**: `/timeline_data/events/*.yaml`
- **API endpoints**: `/viewer/public/api/*.json`

### Is there an API?
Currently, we provide static JSON files that can be fetched directly. A full API is planned for future development.

### Why no backend/database?
Static files ensure:
- Maximum resilience (can't be taken down easily)
- Easy replication (anyone can host a copy)
- Version control (full history in Git)
- No maintenance costs
- Fast performance

## 🤝 Contributing

### How can I contribute?
Several ways:
1. **Add events**: Submit new events via GitHub issues
2. **Verify sources**: Check and archive sources
3. **Fix errors**: Report corrections via issues
4. **Improve code**: Submit pull requests
5. **Share**: Spread awareness of the project

### How do I report a broken link?
Use the GitHub issue template "Report Broken Link" or file an issue with:
- Event ID
- Broken URL
- Error type (404, paywall, etc.)
- Alternative URL if available

### How do I submit a new event?
Use the GitHub issue template "Submit New Event" with:
- Date (YYYY-MM-DD)
- Clear, factual title
- 2-3 sentence summary
- Minimum 2 credible sources
- Relevant capture lanes
- Importance rating (1-10) with justification

### What sources are acceptable?
Credible sources include:
- Major news outlets
- Government documents
- Court filings
- Academic papers
- Official statements
- Archived original documents

Not acceptable:
- Social media posts alone
- Partisan blogs without sources
- Conspiracy websites
- Unverified claims

### How do I run this locally?
```bash
# Clone the repository
git clone https://github.com/markramm/KleptocracyTimeline.git
cd KleptocracyTimeline

# Install and run the viewer
cd viewer
npm install
npm start

# Validate timeline data
cd ../timeline_data
python3 validate_yaml.py
```

## 🛡️ Trust & Verification

### How do I know the data is accurate?
- Every event has multiple sources
- All sources are archived
- YAML files show complete history in Git
- Community can verify and challenge
- Corrections welcomed via issues

### What if I find an error?
Please report it! Use the "Event Correction" issue template or file an issue with:
- Event ID
- What's wrong
- Correct information
- Supporting sources

### Is this project secure?
- All code is open source for inspection
- No user data is collected
- No cookies or tracking (unless analytics added)
- Static site minimizes attack surface
- Multiple copies ensure resilience

### Who reviews contributions?
Currently, project maintainers review all contributions. As the community grows, we'll establish a more formal review process with multiple reviewers for significant changes.

## 🎯 Using the Timeline

### How do I navigate the timeline?
- **Scroll**: Browse chronologically
- **Filter**: Use capture lanes, tags, or date ranges
- **Search**: Find specific events or actors
- **Network View**: See connections between actors
- **Share**: Deep link to specific events

### Can I embed this in my website?
Currently, you can link to specific events using URL parameters. Embeddable widgets are planned for future development.

### How do I cite an event?
Format: `Event Title (Date). Kleptocracy Timeline. Event ID: [ID]. Retrieved from [URL]`

Example: `Supreme Court Overturns Chevron Deference (2024-06-28). Kleptocracy Timeline. Event ID: 2024-06-28--loper-bright-overturns-chevron-deference. Retrieved from https://markramm.github.io/KleptocracyTimeline/?event=2024-06-28--loper-bright-overturns-chevron-deference`

### What do the different status indicators mean?
- **Confirmed**: Verified with 2+ sources
- **Pending**: Awaiting verification
- **Disputed**: Conflicting sources exist
- **Predicted**: Future event not yet occurred

## 🚨 Concerns & Challenges

### What about misinformation?
We combat misinformation through:
- Rigorous source requirements
- Community verification
- Transparent methodology
- Complete audit trail in Git
- Corrections welcomed

### Could this be used maliciously?
We document public information about systemic issues. We explicitly:
- Don't include private information
- Don't call for violence
- Don't spread conspiracy theories
- Focus on institutional patterns, not personal attacks

### What if powerful interests try to stop this?
The project is designed for resilience:
- Open source (anyone can fork)
- Static files (easy to mirror)
- Distributed hosting possible
- Community ownership
- Multiple backups

### Is this legal?
Yes. We only document publicly available information from credible sources. This is journalism, research, and protected speech.

## 📈 Future Development

### What's planned next?
- Source archiving completion
- API development
- Mobile app
- Embeddable widgets
- Advanced visualizations
- Automated verification
- Multi-language support

### How is this funded?
Currently unfunded and volunteer-driven. We're exploring:
- Grants from civil society organizations
- Crowdfunding
- Foundation support
- Academic partnerships

Never through ads or data collection.

### Can I use this for research?
Absolutely! This is open data for:
- Academic research
- Journalism
- Civil society organizations
- Policy analysis
- Educational purposes

Please cite the project in your work.

### How can I stay updated?
- **GitHub**: Star/watch the repository
- **Substack**: https://theramm.substack.com/
- **Issues**: Subscribe to GitHub issues
- **Social**: Follow launch announcements

## 🤖 AI Integration

### How was AI used in this project?
AI assistants helped with:
- Pattern recognition across events
- Data validation and formatting
- Documentation generation
- Analysis acceleration
- Code development

All AI work is verified by humans.

### Can I use AI tools with this data?
Yes! See `/AI_INTEGRATION.md` for guides on using:
- ChatGPT
- Claude
- Cursor
- GitHub Copilot
- Other AI tools

### Does AI make decisions about what to include?
No. Humans make all editorial decisions. AI assists with pattern recognition and validation, but humans verify everything.

## 💪 Support & Community

### How can I support the project?
- **Use it**: View and share the timeline
- **Contribute**: Add events, fix errors
- **Share**: Spread awareness
- **Star**: GitHub repository
- **Defend**: Against attacks or misinformation

### Is there a community?
Growing! Currently:
- GitHub Issues for discussion
- Substack for analysis
- Social media for updates

Planning: Discord or similar for real-time collaboration

### Who do I contact for help?
- **Technical issues**: GitHub Issues
- **Content questions**: GitHub Discussions
- **Press inquiries**: Via GitHub or Substack
- **Security concerns**: Private message to maintainers

### Can I create a local version for my country?
Absolutely! The framework is open source. We encourage:
- Forking for other countries
- Translation to other languages
- Adaptation for regional contexts
- Sharing patterns across projects

---

## Quick Links

- **Live Timeline**: https://markramm.github.io/KleptocracyTimeline/
- **GitHub Repository**: https://github.com/markramm/KleptocracyTimeline
- **Substack**: https://theramm.substack.com/
- **Report Issue**: https://github.com/markramm/KleptocracyTimeline/issues

---

*"Truth is the foundation of democracy. Documentation is the foundation of truth. This timeline is our contribution to both."*