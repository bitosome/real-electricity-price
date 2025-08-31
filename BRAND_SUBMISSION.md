# 🎨 Brand Assets Submission Guide

## 📋 Overview

To display the custom logo/icon for the Real Electricity Price integration in Home Assistant, the brand assets need to be submitted to the official Home Assistant brands repository.

## 🚀 Quick Submission Process

### Step 1: Fork the Brands Repository
1. Go to https://github.com/home-assistant/brands
2. Click **Fork** to create your own copy
3. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/brands.git
   cd brands
   ```

### Step 2: Add Brand Assets
1. Create the integration directory:
   ```bash
   mkdir -p custom_integrations/real_electricity_price
   ```

2. Copy the prepared assets:
   ```bash
   # From your real-electricity-price repository
   cp brands_payload/custom_integrations/real_electricity_price/* custom_integrations/real_electricity_price/
   ```

### Step 3: Submit Pull Request
1. Create a new branch:
   ```bash
   git checkout -b add-real-electricity-price-branding
   ```

2. Add and commit the files:
   ```bash
   git add custom_integrations/real_electricity_price/
   git commit -m "Add Real Electricity Price integration branding"
   ```

3. Push and create PR:
   ```bash
   git push origin add-real-electricity-price-branding
   ```

4. Open a Pull Request at https://github.com/home-assistant/brands/pulls

## 📁 Assets Included

The following files will be submitted:

### `custom_integrations/real_electricity_price/icon.png`
- **Size**: 256×256 pixels
- **Format**: PNG with transparency
- **Design**: Euro coin symbol representing electricity pricing
- **Usage**: Integration list, settings, device tiles

### `custom_integrations/real_electricity_price/logo.png`
- **Size**: 512×512 pixels  
- **Format**: PNG with transparency
- **Design**: Same euro coin symbol at higher resolution
- **Usage**: Integration configuration pages, detailed views

## ✅ Asset Requirements Met

- ✅ **Proper sizing**: 256×256 (icon) and 512×512 (logo)
- ✅ **PNG format**: With transparency support
- ✅ **Clear design**: Euro symbol is recognizable at all sizes
- ✅ **Theme compatibility**: Works on light and dark backgrounds
- ✅ **Brand guidelines**: Follows Home Assistant's visual standards

## 📝 PR Description Template

Use this template for your Pull Request description:

```markdown
# Add Real Electricity Price Integration Branding

## Integration Details
- **Domain**: `real_electricity_price`
- **Name**: Real Electricity Price
- **Repository**: https://github.com/bitosome/real-electricity-price
- **Type**: Custom Integration

## Assets
- `icon.png` (256×256) - Euro coin symbol for electricity pricing
- `logo.png` (512×512) - Higher resolution version

## Design Rationale
The euro coin icon represents the core functionality of real-time electricity pricing in euros for Estonian market integration with Nord Pool data.

## Verification
- [ ] Icons display correctly on light theme
- [ ] Icons display correctly on dark theme
- [ ] Files meet size requirements
- [ ] PNG format with transparency
```

## ⏱️ Timeline

### Immediate (Now)
- ✅ Integration works with default Home Assistant icon
- ✅ Assets prepared and ready for submission
- ✅ Local testing possible with files in integration directory

### After PR Submission
- **1-7 days**: Review by Home Assistant brands team
- **Upon merge**: Icons automatically available globally
- **No restart needed**: Cache refresh updates icons

### After Merge
- ✅ Custom euro coin icon displays in integration list
- ✅ Logo appears in configuration flows
- ✅ Professional branding throughout Home Assistant

## 🔧 Local Testing

For immediate local testing, the icon and logo files are already copied to:
- `custom_components/real_electricity_price/icon.png`
- `custom_components/real_electricity_price/logo.png`

Home Assistant may use these files locally while waiting for the official brands repository merge.

## 📞 Support

If you encounter issues with the brands submission:
- Review the [brands repository guidelines](https://github.com/home-assistant/brands/blob/main/README.md)
- Check existing PRs for examples
- Ask in the Home Assistant Discord #devs_integrations channel

The integration will work perfectly without custom branding - the icons are purely cosmetic improvements for better user experience.
