# Medical UI Design System (MDS) - Version 1.0

**Erstellt für:** Praxis- und Terminplanungssoftware  
**Ziel:** Einheitliches, ruhiges, modernes UI für medizinisches Personal

---

## 1. Designphilosophie

Das Medical Design System (MDS) basiert auf drei Grundprinzipien:

### 🌿 1. Ruhe

Die UI soll Stress reduzieren.
- Helle Flächen
- Weiche Farben
- Klare Typografie
- Viel Weißraum

Diese Elemente schaffen ein ruhiges Arbeitsumfeld.

### 🎯 2. Klarheit

Medizinisches Personal muss schnell Entscheidungen treffen. Deshalb sind alle Komponenten:
- **eindeutig**
- **gut lesbar**
- **logisch gruppiert**
- **frei von visueller Überlastung**

### 🧩 3. Konsistenz

Alle Seiten und Komponenten folgen denselben Regeln:
- Gleiche Abstände
- Gleiche Farben
- Gleiche Typografie
- Gleiche Interaktionen

Das schafft Vertrauen und reduziert Fehler.

---

## 2. Farbpalette

### 🎨 Primärfarben

| Name | Hex | Verwendung |
|------|-----|------------|
| Soft Azure | `#4A90E2` | Primäre Aktionen, Links, Highlights |
| Calm Mint | `#7ED6C1` | Sekundäre Aktionen, Status "Aktiv" |
| Soft Green | `#6FCF97` | Erfolg, Bestätigung, Positive Status |
| Soft Amber | `#F2C94C` | Warnung, Aufmerksamkeit |
| Soft Coral | `#EB5757` | Fehler, Gefahr, Irreversible Aktionen |

### ⚪ Neutrale Farben

| Name | Hex | Verwendung |
|------|-----|------------|
| Background | `#F7F9FB` | Haupt-Hintergrund der Anwendung |
| Cards | `#FFFFFF` | Karten, Panels, Modals |
| Lines | `#E5E9F0` | Trennlinien, Borders |
| Text Dark | `#2D3A45` | Primärer Text, Überschriften |
| Text Light | `#7A8A99` | Sekundärer Text, Platzhalter |

### 🎯 Farbregeln

- **Primärfarbe** nur für wichtige Aktionen
- **Pastellfarben** für Diagramme
- **Keine harten Kontraste**
- **Fehlerfarben** sparsam einsetzen

---

## 3. Typografie

### Schriftfamilie

- **Inter** (empfohlen) - Moderne, gut lesbare Sans-Serif-Schrift
- **Segoe UI** (Windows-freundlich) - Alternative für Windows-Umgebungen

### Textgrößen

| Stil | Größe | Zeilenhöhe | Verwendung |
|------|-------|------------|------------|
| H1 | 32px | 1.4 | Hauptüberschriften |
| H2 | 24px | 1.4 | Sektionsüberschriften |
| H3 | 20px | 1.5 | Unterüberschriften |
| Body Large | 16px | 1.6 | Haupttext |
| Body | 14px | 1.6 | Standardtext |
| Small | 12px | 1.5 | Sekundärer Text, Labels |

### Typografie-Regeln

- **Keine Großbuchstaben** für ganze Wörter
- **Zeilenhöhe** 1.4–1.6
- **Maximal 2 Schriftgrößen** pro Komponente

---

## 4. Spacing & Layout

### Abstände

| Name | Größe | Verwendung |
|------|-------|------------|
| XS | 4px | Sehr kleine Abstände, Icon-Padding |
| S | 8px | Kleine Abstände, kompakte Komponenten |
| M | 16px | Standard-Abstände, Card-Padding |
| L | 24px | Große Abstände, Sektions-Abstände |
| XL | 32px | Sehr große Abstände, Seiten-Abstände |

### Layout-Raster

| Element | Größe | Beschreibung |
|---------|-------|--------------|
| Sidebar | 240px | Navigationsleiste (links) |
| Header | 64px | Top-Navigation |
| Content-Padding | 24px | Padding um Haupt-Content |

### Schatten

| Name | Verwendung |
|------|------------|
| Shadow 1 | Leichte Karte, Standard-Elevation |
| Shadow 2 | Hover-Zustand, erhöhte Karte |
| Shadow 3 | Modal, Dropdown, höchste Elevation |

### Border-Radius

| Element | Radius | Beschreibung |
|---------|--------|--------------|
| Standard | 8px | Allgemeine Komponenten |
| Buttons | 6px | Button-Komponenten |
| Cards | 10px | Karten-Komponenten |

---

## 5. Komponentenbibliothek

### 🟦 Buttons

**Varianten:**
- **Primary** (Soft Azure `#4A90E2`) - Hauptaktion
- **Secondary** (Grey) - Sekundäre Aktion
- **Danger** (Soft Coral `#EB5757`) - Gefährliche/irreversible Aktion
- **Ghost** (Outline) - Tertiäre Aktion

**Regeln:**
- Primary nur für **wichtigste Aktion**
- Danger nur für **irreversible Aktionen**
- Ghost für **sekundäre Aktionen**

**Spezifikationen:**
- Padding: 12px 24px
- Border-Radius: 6px
- Font-Size: 14px
- Font-Weight: 500
- Min-Height: 40px (Barrierefreiheit)

### 🧩 Inputs

**Typen:**
- Textfield
- Dropdown/Select
- Autocomplete
- Datepicker
- Timepicker

**Regeln:**
- **Labels immer sichtbar**
- **Fehlerzustände** in Soft Coral
- **Fokuszustand** mit Soft Azure Border (2px)

**Spezifikationen:**
- Padding: 12px 16px
- Border-Radius: 8px
- Border: 1px solid `#E5E9F0`
- Font-Size: 14px
- Min-Height: 40px

### 🧱 Cards

**Typen:**
- KPI-Card
- Resource-Card
- Patient-Card

**Regeln:**
- Schatten 1
- Radius 10px
- Innenabstand 16–24px

**Spezifikationen:**
- Background: `#FFFFFF`
- Border-Radius: 10px
- Padding: 16px–24px
- Shadow: Shadow 1
- Border: Optional 1px solid `#E5E9F0`

### 📋 Tabellen

**Regeln:**
- Viel Weißraum
- Hover-Effekt
- Zeilenhöhe 48px
- Header fett, 14px

**Spezifikationen:**
- Zeilenhöhe: 48px
- Header: Font-Weight 600, Font-Size 14px
- Body: Font-Size 14px
- Padding (Zellen): 12px 16px
- Border: 1px solid `#E5E9F0`
- Hover: Background `#F7F9FB`

### 📁 Panels & Modals

**Typen:**
- Side Panel (Termin-Details)
- Modal (Termin anlegen)

**Regeln:**
- Weißer Hintergrund
- Schatten 3
- 24px Padding

**Spezifikationen:**
- Background: `#FFFFFF`
- Padding: 24px
- Shadow: Shadow 3
- Border-Radius: 8px (Modal), 0px (Side Panel - Top/Right)

### 📅 Kalender-Komponenten

**Elemente:**
- Event Block
- Time Grid
- Day Header
- Drag-Ghost Element

**Regeln:**
- Farben pro Arzt oder Raum
- Runde Ecken
- Schatten 1

**Spezifikationen:**
- Event Block: Border-Radius 6px, Padding 8px 12px
- Border: Optional 1px solid (Transparenz)
- Shadow: Shadow 1 (bei Hover/Drag)

### 📊 Accordion

**Elemente:**
- Header mit Chevron
- Content mit 16px Padding
- Sanfte Slide-Animation

**Spezifikationen:**
- Header: Padding 16px, Font-Weight 600
- Content: Padding 16px
- Animation: 0.3s ease-in-out
- Border: 1px solid `#E5E9F0`
- Border-Radius: 8px

---

## 6. Interaktionen

### Hover

- **Leichte Aufhellung** (Background +10% heller)
- **Schatten +1** (von Shadow 1 zu Shadow 2)
- **Transition:** 0.2s ease-in-out

### Active

- **Leichte Abdunklung** (Background -5% dunkler)
- **Schatten -1** (von Shadow 2 zu Shadow 1)

### Focus

- **Soft Azure Border** (2px solid `#4A90E2`)
- **Outline:** none (verwendet Border statt Outline)

### Drag & Drop

- **Ghost-Element:** 50% Opacity, Shadow 2
- **Drop-Zonen:** Highlighted mit Soft Azure Border (2px dashed)
- **Cursor:** `grab` (normal), `grabbing` (aktiv)

---

## 7. Barrierefreiheit

### Kontrast

- **Mindestkontrast:** 4.5:1 (WCAG AA)
- Text auf Background: Mindestens 4.5:1
- Großtext (18px+): Mindestens 3:1

### Interaktion

- **Klickflächen ≥ 40px** (Höhe und Breite)
- **Abstand zwischen klickbaren Elementen:** Mindestens 8px

### Fokus

- **Klare Fokuszustände** (Soft Azure Border 2px)
- **Keyboard-Navigation:** Alle interaktiven Elemente erreichbar

### Farbinformationen

- **Keine rein farbbasierten Informationen**
- Icons oder Text als zusätzliche Indikatoren

---

## 8. Anwendungsbeispiele

### Terminplanung

- **Drag & Drop:** Termine verschieben
- **Resize:** Termin-Dauer ändern
- **Autocomplete:** Patient/Arzt/Raum auswählen
- **Side Panel:** Termin-Details anzeigen

### Patientenliste

- **Tabelle** mit Suchfeld
- **Filter:** Status, Risiko, etc.
- **Hover-Effekte:** Zeilen hervorheben

### Dashboard

- **KPI-Karten:** Übersichtliche Metriken
- **Accordion-Diagramme:** Kollabierbare Statistiken

---

## 9. Erweiterbarkeit

Dieses Designsystem ist modular aufgebaut und kann erweitert werden um:

- **Dark Mode:** Alternative Farbpalette für dunkle Umgebungen
- **Mobile Layouts:** Responsive Breakpoints und Komponenten
- **Mehrsprachigkeit:** RTL-Support, längere Texte
- **Rollenbasierte UI-Varianten:** Anpassungen je nach Benutzerrolle

---

## 10. Implementierung

### CSS-Variablen (Design Tokens)

Die Farben, Abstände und Typografie werden als CSS Custom Properties definiert:

```css
:root {
  /* Primary Colors */
  --color-primary-azure: #4A90E2;
  --color-primary-mint: #7ED6C1;
  --color-primary-green: #6FCF97;
  --color-primary-amber: #F2C94C;
  --color-primary-coral: #EB5757;
  
  /* Neutral Colors */
  --color-bg: #F7F9FB;
  --color-card: #FFFFFF;
  --color-line: #E5E9F0;
  --color-text-dark: #2D3A45;
  --color-text-light: #7A8A99;
  
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-s: 8px;
  --spacing-m: 16px;
  --spacing-l: 24px;
  --spacing-xl: 32px;
  
  /* Layout */
  --sidebar-width: 240px;
  --header-height: 64px;
  --content-padding: 24px;
  
  /* Border Radius */
  --radius-standard: 8px;
  --radius-button: 6px;
  --radius-card: 10px;
  
  /* Shadows */
  --shadow-1: 0 2px 4px rgba(0, 0, 0, 0.08);
  --shadow-2: 0 4px 8px rgba(0, 0, 0, 0.12);
  --shadow-3: 0 8px 16px rgba(0, 0, 0, 0.16);
}
```

### Dateien

- `design-tokens-modern.css` - CSS Custom Properties
- `components-modern.css` - Komponenten-Styles
- `base-modern.css` - Basis-Styles (Typography, Layout)

---

## Version

**Version 1.0** - Erstellt: 2026-01-04

---

## Changelog

### Version 1.0 (2026-01-04)
- Initiale Version des Medical UI Design Systems
- Definition von Farben, Typografie, Spacing, Komponenten
- Barrierefreiheits-Richtlinien
- Erweiterbarkeits-Konzepte

