# ToolUniverse Scientific Research Examples

This directory contains professional scientific research examples demonstrating the use of ToolUniverse's direct import functionality for real-world scientific applications.

## Overview

The examples showcase how to use `tooluniverse.tools` direct imports to build comprehensive scientific research workflows with proper data flow and scientific rigor.

## Professional Workflow Examples

All workflows are located in the `examples/workflows/` directory and demonstrate professional scientific research methodologies with direct tool usage.

### 1. Drug Discovery Workflow (`workflows/drug_discovery.py`)

**Complete drug discovery pipeline with target ranking and mechanism analysis**

- **Purpose**: Professional drug discovery for precision medicine
- **Key Features**:
  - Disease target identification and ranking using OpenTargets
  - Drug similarity search using ChEMBL
  - Comprehensive ADMET property prediction with composite scoring
  - Drug mechanism analysis and target overlap calculation
  - Clinical evidence synthesis and literature support
  - Structured output with scientific metrics
- **Example**: Type 2 diabetes drug discovery using Metformin as reference

### 2. Biomarker Discovery Workflow (`workflows/biomarker_discovery.py`)

**Cancer biomarker discovery with network analysis and pathway enrichment**

- **Purpose**: Professional biomarker discovery for cancer research
- **Key Features**:
  - Gene expression analysis using HPA
  - Protein-protein interaction analysis using HumanBase
  - Pathway enrichment analysis with statistical filtering (q<0.05)
  - Literature search for biomarker evidence
  - Composite scoring system for biomarker prioritization
- **Example**: Breast cancer biomarker discovery for BRCA1, BRCA2, TP53, PTEN, PIK3CA

### 3. Precision Medicine Workflow (`workflows/precision_medicine.py`)

**Patient genomic variant analysis and personalized therapy matching**

- **Purpose**: Precision medicine for personalized treatment
- **Key Features**:
  - Patient genetic variant analysis
  - Disease target identification and overlap analysis
  - Drug response prediction simulation
  - Clinical trial matching with eligibility criteria
  - Personalized treatment recommendations
- **Example**: Patient with specific genetic variants for disease treatment

### 4. Gene Expression Analysis Workflow (`workflows/gene_expression_analysis.py`)

**Comprehensive gene expression analysis using HPA (Human Protein Atlas)**

- **Purpose**: Professional gene expression profiling and analysis
- **Key Features**:
  - Gene information retrieval and validation
  - Comprehensive gene details and annotations
  - Comparative expression analysis across cell lines
  - Cancer prognostic significance analysis
  - Biological process analysis
  - Disease-specific expression analysis
  - Pathway enrichment analysis
- **Example**: Breast cancer gene expression analysis for BRCA1, BRCA2, TP53, PTEN, PIK3CA

### 5. Protein Interaction Analysis Workflow (`workflows/protein_interaction_analysis.py`)

**Comprehensive protein-protein interaction analysis using HumanBase**

- **Purpose**: Professional protein network analysis and functional annotation
- **Key Features**:
  - Gene validation and Ensembl ID mapping
  - Protein-protein interaction network analysis
  - Gene annotation analysis with GO terms
  - Pathway enrichment analysis
  - Network statistics and highly connected gene identification
- **Example**: Breast cancer protein interaction analysis for BRCA1, BRCA2, TP53, PTEN, PIK3CA

### 6. Clinical Guidelines Search Workflow (`workflows/clinical_guidelines_search.py`)

**Multi-source clinical guidelines search and analysis**

- **Purpose**: Evidence-based clinical decision support
- **Key Features**:
  - Search across 7 major guideline sources (NICE, PubMed, EuropePMC, OpenAlex, SemanticScholar, EvidenceBased, WHO)
  - Guideline standardization and deduplication
  - Citation-based ranking and analysis
  - Summary statistics and source comparison
  - Top guideline compilation
- **Example**: Diabetes management guidelines search

### 7. Literature Review Workflow (`workflows/literature_review.py`)

**Comprehensive literature review across multiple academic databases**

- **Purpose**: Professional literature review and evidence synthesis
- **Key Features**:
  - Search across 5 academic databases (ArXiv, PubMed, EuropePMC, SemanticScholar, OpenAlex)
  - Paper deduplication and standardization
  - Citation-based ranking and analysis
  - Open access analysis
  - Publication year distribution
  - Source comparison and statistics
- **Example**: Machine learning in drug discovery literature review

## Cache Demonstrations

- ``cache_usage_example.py`` — Step-by-step walkthrough of enabling caching, inspecting stats, and clearing results.
- ``cache_stress_test.py`` — Randomized load generator that measures cache hit rates and timing performance under repeated calls.

## Key Features

### Professional Quality
- **Scientific Rigor**: Examples demonstrate real-world scientific research methodologies
- **Data Flow**: Proper use of output from one step as input for the next
- **Error Handling**: Robust error handling for production use
- **Documentation**: Comprehensive docstrings and comments

### Direct Tool Usage
- **No Wrappers**: Direct import and use of `tooluniverse.tools` functions
- **Clean Code**: Minimal, readable code without unnecessary abstractions
- **Efficient**: Direct function calls without overhead

### Comprehensive Coverage
- **Multiple Domains**: Drug discovery, genomics, literature, protein structure, clinical trials
- **Tool Integration**: Seamless integration of multiple scientific tools
- **Real Data**: Uses actual scientific databases and APIs

## Usage

### Running Workflows

```bash
# Run individual professional workflows
python examples/workflows/drug_discovery.py
python examples/workflows/biomarker_discovery.py
python examples/workflows/precision_medicine.py
python examples/workflows/gene_expression_analysis.py
python examples/workflows/protein_interaction_analysis.py
python examples/workflows/clinical_guidelines_search.py
python examples/workflows/literature_review.py

# Run all workflows (if you have a batch script)
# Each workflow can be run independently
```

### Key Dependencies

```python
from tooluniverse.tools import (
    OpenTargets_get_disease_id_description_by_name,
    OpenTargets_get_associated_targets_by_disease_efoId,
    ChEMBL_search_similar_molecules,
    FDA_get_drug_names_by_indication,
    EuropePMC_search_articles,
    HPA_search_genes_by_query,
    GO_get_annotations_for_gene,
    search_clinical_trials,
    ADMETAI_predict_toxicity,
    ADMETAI_predict_bioavailability
)
```

## Scientific Value

These examples demonstrate:

1. **Real Research Applications**: Actual scientific workflows used in research
2. **Tool Integration**: How to combine multiple scientific tools effectively
3. **Data Pipeline**: Proper data flow and processing
4. **Professional Standards**: Code quality suitable for scientific publications
5. **Reproducibility**: Clear, documented workflows that can be reproduced

## Best Practices Demonstrated

- **Direct Tool Usage**: Import and use tools directly without unnecessary wrappers
- **Error Handling**: Robust error handling for production use
- **Data Validation**: Proper checking of tool outputs before use
- **Scientific Methodology**: Following established scientific research practices
- **Code Quality**: Clean, readable, and maintainable code

## Target Audience

- **Researchers**: Scientists looking to integrate multiple tools in their research
- **Developers**: Software developers building scientific applications
- **Students**: Graduate students learning scientific computing
- **Professionals**: Industry professionals in biotech and pharma

## Contributing

When adding new examples:

1. Follow the established patterns for direct tool usage
2. Ensure proper data flow between steps
3. Include comprehensive error handling
4. Add clear documentation and comments
5. Test thoroughly before submission

## License

These examples are part of the ToolUniverse project and follow the same licensing terms.
