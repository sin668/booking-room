# DESIGN.md

## Colors

- Primary: #4F6EF7 (OKLCH approximation)
- Primary light: #E8EDFF
- Primary dark: #3A56D4
- Background: #F5F6FA
- Text primary: #2D3436
- Text secondary: #636E72
- Text muted: #B2BEC3
- Success: #07C160
- Danger: #FF6B6B
- Purple accent: #6C5CE7

Color strategy: Restrained. Single accent (primary) used for actions, selections, and active states. Semantic colors for status only.

## Typography

- System font stack: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif
- One family, no display/body pairing
- Scale ratio ~1.2 between steps
- Chinese body text at 26-28rpx, headings at 30-36rpx

## Spacing & Radius

- Content margin: 28rpx horizontal
- Card radius: 20-24rpx
- Button radius: 16rpx (rectangular) / 44rpx (pill)
- Tag radius: 20-24rpx (pill)
- Section gap: 24-32rpx

## Shadows

- Cards: 0 4rpx 16rpx rgba(0,0,0,0.04)
- Elevated: 0 8rpx 24rpx rgba(79,110,247,0.12) or rgba(0,0,0,0.06)

## Components

- Cards: white background, 20-24rpx radius, subtle shadow
- Buttons: pill-shaped primary actions, rectangular secondary
- Tags: pill-shaped, tinted background with matching text color
- Status badges: tinted background, small rounded

## Icons

- Prototype: Font Awesome 6.5.1
- App: custom iconfont via `<view class="icon icon-xxx" />` pattern
