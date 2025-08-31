# Integration Branding (Icon & Logo)

This project follows Home Assistant's branding system. Integration icons and logos shown in the UI are served from the central brands repository.

## ✅ Current Status

Your euro coin icon is now properly prepared at:
- **Source**: `assets/icon.png` (your provided icon)
- **Generated**: `brands_payload/custom_integrations/real_electricity_price/`
  - `icon.png` (256×256 px)
  - `logo.png` (512×512 px)

## Use this image as the integration icon

To make Home Assistant show your euro coin icon for this custom integration:

1. **Assets are ready** ✅ (already generated in `brands_payload/`)
2. **Fork** https://github.com/home-assistant/brands
3. **Copy the folder**: Copy `brands_payload/custom_integrations/real_electricity_price/` to your fork
4. **Submit PR**: Open a Pull Request to the brands repository
5. **Wait for merge**: After approval, Home Assistant will automatically display your icon

## Testing locally (optional)

For development testing, you can verify your icon looks good by viewing `assets/icon.png` or the generated files in `brands_payload/`.

## Timeline

- **Immediately**: Integration works with default puzzle piece icon
- **After brands PR merge**: Your custom euro coin icon appears automatically
- **No restart needed**: Icons update via cache refresh

Notes:
- The euro coin icon has good contrast and should work well on both light/dark themes
- Generated assets follow Home Assistant's size requirements (256×256, 512×512)
- Integration functionality is not affected by icon status