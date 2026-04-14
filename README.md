# Technical Animation & Rigging Portfolio (Maya Python)

## Overview
This repository showcases a collection of rigging systems, deformation studies, and pipeline tools developed in Autodesk Maya using Python. 

The work focuses on creating animator-friendly rigs, exploring deformation techniques, and building tools to automate and streamline rigging workflows.

---

## Rigging Projects

### Character Rig (IK/FK System)
A fully functional character rig featuring a modular IK/FK system designed for animation flexibility and stability.

**Features:**
- Seamless IK ↔ FK switching
- Tail rig using Maya's hair system
- Clean control hierarchy for animator usability

---

### Facial Rig (Viseme-Based)
A facial rig designed for expressive animation, with a focus on mouth shapes and speech-driven deformation.

**Features:**
- Viseme-based controls for dialogue animation
- Blendshape driven movement
- Designed for clean interpolation between expressions

---

### Deformation Rig (Flour Sack)
A stylized deformation rig exploring squash and stretch principles.

**Features:**
- Procedural squash and stretch behavior
- Volume preservation during deformation

---

## Tools & Scripts

### IK/FK Builder Tool
A reusable tool for generating IK/FK systems on custom joint hierarchies.

**Features:**
- Works on arbitrary joint chains
- Custom control size and color selection via UI
- Automated constraint setup
- Designed for reuse across different rigs

**Includes:**
- Example joint hierarchy file for testing and demonstration

---

### Export Script
A utility script for streamlining asset export and validation.

**Features:**
- Automated export workflow
- Pivot adjustment
- Basic scene validation checks
- Designed to reduce manual setup and errors

---

## Tools & Technologies
- Autodesk Maya
- Python (`maya.cmds`)
- Maya UI scripting
- Git / GitHub for version control

---

## Repository Structure
