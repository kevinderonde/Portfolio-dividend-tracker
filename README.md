# Portfolio Dividend Tracker for Home Assistant

Unofficial community integration for Portfolio Dividend Tracker (PDT). Uses the PDT read-only API to expose portfolio summary sensors and an on-demand API query action. Not affiliated with or endorsed by PDT.

## Installation

1. Copy `custom_components/portfolio_dividend_tracker` to your Home Assistant `/config/custom_components/` directory, or add this repository as a custom repository in your supported community store.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**, search for **Portfolio Dividend Tracker**, and enter your personal API token.

Never publish your API token. If a token was exposed, revoke and replace it.

## Features

- Portfolio summary sensors refreshed every 15 minutes.
- On-demand `portfolio_dividend_tracker.get_data` action for supported read-only resources.
- Response data can include sensitive financial information.

Example action:

```yaml
action: portfolio_dividend_tracker.get_data
data:
  resource: transactions
```

## Support

[Report an issue](https://github.com/kevinderonde/Portfolio-dividend-tracker/issues).

## License

MIT (see LICENSE in this repository).
