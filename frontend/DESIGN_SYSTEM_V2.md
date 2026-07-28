---
Document Status: ACTIVE
Version: 2.0.0
Owner: Product Design Team
Approval Status: APPROVED
Last Updated: 2026-07-11
Next Review: 2027-01-01
---

# aegisOS Enterprise Design System v2

## Purpose

This document defines the visual language of aegisOS.

Every UI implementation must follow this document.

Do NOT redesign individual pages.

Build reusable components.

The UI should feel like it was designed by an enterprise product team.

Never look AI-generated.

---

# Design Philosophy

aegisOS is

NOT

CRM

ERP

Dashboard

Admin Template

Bootstrap Theme

School Project

aegisOS is

Enterprise AI Operating System.

Everything should communicate

Professional

Modern

Premium

Minimal

Focused

---

# Design Inspiration

Primary

• Linear

• OpenAI Platform

• GitHub

• Notion

• Vercel

Secondary

• Frappe UI

• Stripe Dashboard

Do NOT copy any product.

Only adopt design principles.

---

# Theme

Enterprise Light

Background

#F8FAFC

Surface

#FFFFFF

Sidebar

#F5F7FA

Hover

#EEF2FF

Border

#E5E7EB

Primary

#2563EB

Success

#16A34A

Warning

#F59E0B

Danger

#DC2626

Info

#0EA5E9

Text Primary

#111827

Text Secondary

#6B7280

Muted

#9CA3AF

---

# Typography

Font

Inter

Weights

400

500

600

700

Sizes

12

14

16

18

20

24

30

36

Rules

Large titles only once.

Everything else uses hierarchy.

Avoid bold everywhere.

---

# Spacing

Use 8px grid.

Allowed

4

8

12

16

24

32

48

64

Never random spacing.

---

# Border Radius

Cards

12px

Buttons

10px

Inputs

10px

Drawers

16px

Dialogs

16px

---

# Shadows

Very subtle.

Never heavy.

Use elevation only for

Dialogs

Dropdowns

Drawers

Never shadow every card.

---

# Cards

Avoid

Card inside Card inside Card.

Instead

Header

↓

Content

↓

Footer

Only important information gets a card.

---

# Page Layout

Every page

Executive Header

↓

Metric Strip

↓

Primary Content

↓

Secondary Panels

↓

Timeline / Activity

Never place everything inside bordered containers.

---

# Navigation

Sidebar

Compact

Professional

Single icon family

No oversized icons.

No colorful navigation.

---

# Tables

GitHub style.

Minimal borders.

Sticky header.

Hover highlight.

Inline actions.

Compact rows.

Never use oversized table padding.

---

# Forms

Label above field.

One column unless required.

Large whitespace.

Avoid unnecessary borders.

Group related fields.

---

# Buttons

One Primary button.

Everything else

Secondary

Ghost

Text

Icon

Do not place multiple primary buttons together.

---

# Icons

Use only Ant Design Icons.

One icon style across application.

No emoji.

No mixed icon packs.

---

# KPI Cards

Compact.

Show

Title

Value

Trend

Context

Example

Running Employees

42

+5 Today

Avoid large decorative graphics.

---

# Headers

Every page starts with

Title

Subtitle

Breadcrumb

Status

Actions

Never start with cards.

---

# Drawers

Profile layout.

Header

↓

Identity

↓

Quick Stats

↓

Tabs

Tabs

Overview

Skills

Knowledge

Memory

Policies

Connectors

Tasks

Logs

Artifacts

Analytics

---

# Timeline

GitHub inspired.

Chronological.

Minimal.

Human

AI

System

Different colors.

---

# Activity Feed

Slack style.

Avatar

Actor

Action

Timestamp

Expandable details.

---

# AI Panels

Never expose raw reasoning.

Display

Business Understanding

Confidence

Risks

Recommendations

Next Actions

Hide chain-of-thought.

---

# Graphs

Execution Graph

Hierarchy Graph

Timeline

Should be clean.

Minimal connectors.

No decorative lines.

---

# Empty States

Every page requires

Illustration/Icon

Title

Description

Suggested Action

Never blank screens.

---

# Loading States

Skeletons.

Never spinning loader in middle of page.

---

# Search

Always top-right.

Debounced.

Placeholder examples.

---

# Filters

Compact toolbar.

Never consume excessive space.

---

# Dialogs

Maximum width

720px

Clear title

Description

Primary action

Cancel

---

# Sustainability

Always display together

Tokens

AI Cost

CO₂

Water

Energy

Trees

Never split these across pages.

---

# Accessibility

Keyboard navigation.

Visible focus.

Contrast compliant.

Clickable targets minimum 40px.

---

# Responsiveness

Desktop first.

Tablet supported.

Mobile not required for demo.

---

# Animations

Very subtle.

150–250ms.

No flashy animations.

---

# Reusable Components

ExecutiveHeader

MetricStrip

EntityHeader

EntityCard

InsightCard

StatusBadge

SmartTable

Timeline

ActivityFeed

DocumentViewer

ApprovalPanel

DiscussionPanel

ExecutionGraph

LifecycleStepper

ActionToolbar

EntityDrawer

SearchToolbar

FilterToolbar

LoadingState

EmptyState

These components must be reused everywhere.

---

# Things to Avoid

Bootstrap appearance

Material Dashboard appearance

Card overload

Random colors

Random spacing

Gradient abuse

Large shadows

Huge buttons

Huge icons

Centered dashboards

Placeholder text

AI-generated layouts

---

# Definition of Done

A new user should believe

This is a professionally designed enterprise SaaS platform.

They should NOT be able to identify that AI generated the implementation.

Consistency is more important than visual complexity.

# Migration Strategy

Phase 1: Create reusable components.
Phase 2: Migrate pages one by one.
Phase 3: Remove duplicated inline styles.
Phase 4: Remove deprecated UI code.

# UI Modernization Rules

This project is currently in UI Modernization Mode.

The goal is NOT redesign.

The goal is NOT layout replacement.

The goal is NOT changing the business flow.

The goal is NOT changing the Figma structure.

Only improve visual quality.

Allowed

✓ Light Theme

✓ Better typography

✓ Better spacing

✓ Better colors

✓ Better buttons

✓ Better cards

✓ Better tables

✓ Better forms

✓ Better shadows

✓ Better hover effects

✓ Better empty states

✓ Better loading states

Not Allowed

✗ Moving sections

✗ Removing components

✗ Creating new layouts

✗ Replacing business flow

✗ Changing navigation

✗ Changing page hierarchy

✗ Changing routing

✗ Changing lifecycle

✗ Changing Figma page structure

Rule

If a user compares the page with the Figma,
the layout should remain recognizable.
Only the visual polish should improve.