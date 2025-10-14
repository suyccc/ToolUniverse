from importlib.metadata import version
import warnings
from typing import Any, Optional, List
from .execute_function import ToolUniverse
from .base_tool import BaseTool
from .default_config import default_tool_files

# Version information - read from package metadata or pyproject.toml
__version__ = version("tooluniverse")
from .tool_registry import register_tool, get_tool_registry

# Import tools with graceful fallback
try:
    from . import tools

    _TOOLS_AVAILABLE = True
except ImportError:
    _TOOLS_AVAILABLE = False
    tools = None  # type: ignore

# Check if lazy loading is enabled
# LAZY_LOADING_ENABLED = os.getenv('TOOLUNIVERSE_LAZY_LOADING', 'true').lower() in ('true', '1', 'yes')
LAZY_LOADING_ENABLED = (
    False  # LAZY LOADING DISABLED BECAUSE IT'S STILL UNDER DEVELOPMENT
)

# Import MCP functionality
try:
    from .mcp_integration import _patch_tooluniverse

    # Automatically patch ToolUniverse with MCP methods
    _patch_tooluniverse()

except ImportError:
    # MCP functionality not available
    pass

# Import SMCP with graceful fallback and consistent signatures for type checking
try:
    from .smcp import SMCP, create_smcp_server

    _SMCP_AVAILABLE = True
except ImportError:
    _SMCP_AVAILABLE = False

    class SMCP:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError(
                "SMCP requires FastMCP. Install with: pip install fastmcp"
            )

    def create_smcp_server(
        name: str = "SMCP Server",
        tool_categories: Optional[List[str]] = None,
        search_enabled: bool = True,
        **kwargs: Any,
    ) -> SMCP:
        raise ImportError("SMCP requires FastMCP. Install with: pip install fastmcp")


class _LazyImportProxy:
    """A proxy that lazily imports modules and returns the requested class only when accessed."""

    def __init__(self, module_name, class_name):
        self._module_name = module_name
        self._class_name = class_name
        self._cached_class = None

    def __call__(self, *args, **kwargs):
        """When the class is instantiated, import the module and create the instance."""
        if self._cached_class is None:
            try:
                import importlib

                module = importlib.import_module(
                    f".{self._module_name}", package="tooluniverse"
                )
                self._cached_class = getattr(module, self._class_name)
            except (ImportError, AttributeError) as e:
                raise ImportError(
                    f"Failed to lazily import {self._class_name} from {self._module_name}: {e}"
                )

        return self._cached_class(*args, **kwargs)

    def __getattr__(self, name):
        """Forward attribute access to the actual class after importing."""
        if self._cached_class is None:
            try:
                import importlib

                module = importlib.import_module(
                    f".{self._module_name}", package="tooluniverse"
                )
                self._cached_class = getattr(module, self._class_name)
            except (ImportError, AttributeError) as e:
                raise ImportError(
                    f"Failed to lazily import {self._class_name} from {self._module_name}: {e}"
                )

        return getattr(self._cached_class, name)


# Only import tool classes if lazy loading is disabled
MonarchTool: Any
MonarchDiseasesForMultiplePhenoTool: Any
ClinicalTrialsSearchTool: Any
ClinicalTrialsDetailsTool: Any
OpentargetTool: Any
OpentargetGeneticsTool: Any
OpentargetToolDrugNameMatch: Any
DiseaseTargetScoreTool: Any
FDADrugLabelTool: Any
FDADrugLabelSearchTool: Any
FDADrugLabelSearchIDTool: Any
FDADrugLabelGetDrugGenericNameTool: Any
FDADrugAdverseEventTool: Any
FDACountAdditiveReactionsTool: Any
ChEMBLTool: Any
EuropePMCTool: Any
SemanticScholarTool: Any
PubTatorTool: Any
EFOTool: Any
AgenticTool: Any
DatasetTool: Any
SearchSPLTool: Any
GetSPLBySetIDTool: Any
HPAGetGeneJSONTool: Any
HPAGetGeneXMLTool: Any
ReactomeRESTTool: Any
PubChemRESTTool: Any
URLHTMLTagTool: Any
URLToPDFTextTool: Any
MedlinePlusRESTTool: Any
UniProtRESTTool: Any
PackageTool: Any
USPTOOpenDataPortalTool: Any
XMLDatasetTool: Any
ToolFinderEmbedding: Any
ToolFinderKeyword: Any
ToolFinderLLM: Any
EmbeddingDatabase: Any
EmbeddingSync: Any
RCSBTool: Any
GWASAssociationSearch: Any
GWASStudySearch: Any
GWASSNPSearch: Any
GWASAssociationByID: Any
GWASStudyByID: Any
GWASSNPByID: Any
GWASVariantsForTrait: Any
GWASAssociationsForTrait: Any
GWASAssociationsForSNP: Any
GWASStudiesForTrait: Any
GWASSNPsForGene: Any
GWASAssociationsForStudy: Any
MCPClientTool: Any
MCPAutoLoaderTool: Any
ADMETAITool: Any
AlphaFoldRESTTool: Any
ComposeTool: Any
CellosaurusSearchTool: Any
CellosaurusQueryConverterTool: Any
CellosaurusGetCellLineInfoTool: Any
TextEmbeddingTool: Any
if not LAZY_LOADING_ENABLED:
    # Import all tool classes immediately (old behavior) with warning suppression  # noqa: E501
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", category=FutureWarning)

        from .restful_tool import MonarchTool, MonarchDiseasesForMultiplePhenoTool
        from .ctg_tool import ClinicalTrialsSearchTool, ClinicalTrialsDetailsTool
        from .graphql_tool import (
            OpentargetTool,
            OpentargetGeneticsTool,
            OpentargetToolDrugNameMatch,
            DiseaseTargetScoreTool,
        )
        from .openfda_tool import (
            FDADrugLabelTool,
            FDADrugLabelSearchTool,
            FDADrugLabelSearchIDTool,
            FDADrugLabelGetDrugGenericNameTool,
        )
        from .openfda_adv_tool import (
            FDADrugAdverseEventTool,
            FDACountAdditiveReactionsTool,
        )
        from .chem_tool import ChEMBLTool
        from .compose_tool import ComposeTool
        from .europe_pmc_tool import EuropePMCTool
        from .semantic_scholar_tool import SemanticScholarTool
        from .pubtator_tool import PubTatorTool
        from .efo_tool import EFOTool
        from .agentic_tool import AgenticTool
        from .dataset_tool import DatasetTool
        from .dailymed_tool import SearchSPLTool, GetSPLBySetIDTool
        from .hpa_tool import HPAGetGeneJSONTool, HPAGetGeneXMLTool
        from .reactome_tool import ReactomeRESTTool
        from .pubchem_tool import PubChemRESTTool
        from .url_tool import URLHTMLTagTool, URLToPDFTextTool
        from .medlineplus_tool import MedlinePlusRESTTool
        from .uniprot_tool import UniProtRESTTool
        from .package_tool import PackageTool
        from .uspto_tool import USPTOOpenDataPortalTool
        from .xml_tool import XMLDatasetTool
        from .tool_finder_embedding import ToolFinderEmbedding
        from .tool_finder_keyword import ToolFinderKeyword
        from .tool_finder_llm import ToolFinderLLM
        from .embedding_database import EmbeddingDatabase
        from .embedding_sync import EmbeddingSync
        from .rcsb_pdb_tool import RCSBTool
        from .gwas_tool import (
            GWASAssociationSearch,
            GWASStudySearch,
            GWASSNPSearch,
            GWASAssociationByID,
            GWASStudyByID,
            GWASSNPByID,
            GWASVariantsForTrait,
            GWASAssociationsForTrait,
            GWASAssociationsForSNP,
            GWASStudiesForTrait,
            GWASSNPsForGene,
            GWASAssociationsForStudy,
        )
        from .text_embedding_tool import TextEmbeddingTool

    from .mcp_client_tool import MCPClientTool, MCPAutoLoaderTool
    from .admetai_tool import ADMETAITool
    from .alphafold_tool import AlphaFoldRESTTool
    from .odphp_tool import (
        ODPHPMyHealthfinder,
        ODPHPItemList,
        ODPHPTopicSearch,
        ODPHPOutlinkFetch,
    )
    from .cellosaurus_tool import (
        CellosaurusSearchTool,
        CellosaurusQueryConverterTool,
        CellosaurusGetCellLineInfoTool,
    )

    # Literature search tools
    from .arxiv_tool import ArXivTool
    from .crossref_tool import CrossrefTool
    from .dblp_tool import DBLPTool
    from .pubmed_tool import PubMedTool
    from .doaj_tool import DOAJTool
    from .unpaywall_tool import UnpaywallTool
    from .biorxiv_tool import BioRxivTool
    from .medrxiv_tool import MedRxivTool
    from .hal_tool import HALTool
    from .core_tool import CoreTool
    from .pmc_tool import PMCTool
    from .zenodo_tool import ZenodoTool
else:
    # With lazy loading, create lazy import proxies that import modules only when accessed
    MonarchTool = _LazyImportProxy("restful_tool", "MonarchTool")
    MonarchDiseasesForMultiplePhenoTool = _LazyImportProxy(
        "restful_tool", "MonarchDiseasesForMultiplePhenoTool"
    )
    ClinicalTrialsSearchTool = _LazyImportProxy("ctg_tool", "ClinicalTrialsSearchTool")
    ClinicalTrialsDetailsTool = _LazyImportProxy(
        "ctg_tool", "ClinicalTrialsDetailsTool"
    )
    OpentargetTool = _LazyImportProxy("graphql_tool", "OpentargetTool")
    OpentargetGeneticsTool = _LazyImportProxy("graphql_tool", "OpentargetGeneticsTool")
    OpentargetToolDrugNameMatch = _LazyImportProxy(
        "graphql_tool", "OpentargetToolDrugNameMatch"
    )
    DiseaseTargetScoreTool = _LazyImportProxy("graphql_tool", "DiseaseTargetScoreTool")
    FDADrugLabelTool = _LazyImportProxy("openfda_tool", "FDADrugLabelTool")
    FDADrugLabelSearchTool = _LazyImportProxy("openfda_tool", "FDADrugLabelSearchTool")
    FDADrugLabelSearchIDTool = _LazyImportProxy(
        "openfda_tool", "FDADrugLabelSearchIDTool"
    )
    FDADrugLabelGetDrugGenericNameTool = _LazyImportProxy(
        "openfda_tool", "FDADrugLabelGetDrugGenericNameTool"
    )
    FDADrugAdverseEventTool = _LazyImportProxy(
        "openfda_adv_tool", "FDADrugAdverseEventTool"
    )
    FDACountAdditiveReactionsTool = _LazyImportProxy(
        "openfda_adv_tool", "FDACountAdditiveReactionsTool"
    )
    ChEMBLTool = _LazyImportProxy("chem_tool", "ChEMBLTool")
    ComposeTool = _LazyImportProxy("compose_tool", "ComposeTool")
    EuropePMCTool = _LazyImportProxy("europe_pmc_tool", "EuropePMCTool")
    SemanticScholarTool = _LazyImportProxy(
        "semantic_scholar_tool", "SemanticScholarTool"
    )
    PubTatorTool = _LazyImportProxy("pubtator_tool", "PubTatorTool")
    EFOTool = _LazyImportProxy("efo_tool", "EFOTool")
    AgenticTool = _LazyImportProxy("agentic_tool", "AgenticTool")
    DatasetTool = _LazyImportProxy("dataset_tool", "DatasetTool")
    SearchSPLTool = _LazyImportProxy("dailymed_tool", "SearchSPLTool")
    GetSPLBySetIDTool = _LazyImportProxy("dailymed_tool", "GetSPLBySetIDTool")
    HPAGetGeneJSONTool = _LazyImportProxy("hpa_tool", "HPAGetGeneJSONTool")
    HPAGetGeneXMLTool = _LazyImportProxy("hpa_tool", "HPAGetGeneXMLTool")
    ReactomeRESTTool = _LazyImportProxy("reactome_tool", "ReactomeRESTTool")
    PubChemRESTTool = _LazyImportProxy("pubchem_tool", "PubChemRESTTool")
    URLHTMLTagTool = _LazyImportProxy("url_tool", "URLHTMLTagTool")
    URLToPDFTextTool = _LazyImportProxy("url_tool", "URLToPDFTextTool")
    MedlinePlusRESTTool = _LazyImportProxy("medlineplus_tool", "MedlinePlusRESTTool")
    UniProtRESTTool = _LazyImportProxy("uniprot_tool", "UniProtRESTTool")
    PackageTool = _LazyImportProxy("package_tool", "PackageTool")
    USPTOOpenDataPortalTool = _LazyImportProxy("uspto_tool", "USPTOOpenDataPortalTool")
    XMLDatasetTool = _LazyImportProxy("xml_tool", "XMLDatasetTool")
    ToolFinderEmbedding = _LazyImportProxy(
        "tool_finder_embedding", "ToolFinderEmbedding"
    )
    ToolFinderKeyword = _LazyImportProxy("tool_finder_keyword", "ToolFinderKeyword")
    ToolFinderLLM = _LazyImportProxy("tool_finder_llm", "ToolFinderLLM")
    EmbeddingDatabase = _LazyImportProxy("embedding_database", "EmbeddingDatabase")
    EmbeddingSync = _LazyImportProxy("embedding_sync", "EmbeddingSync")
    RCSBTool = _LazyImportProxy("rcsb_pdb_tool", "RCSBTool")
    GWASAssociationSearch = _LazyImportProxy("gwas_tool", "GWASAssociationSearch")
    GWASStudySearch = _LazyImportProxy("gwas_tool", "GWASStudySearch")
    GWASSNPSearch = _LazyImportProxy("gwas_tool", "GWASSNPSearch")
    GWASAssociationByID = _LazyImportProxy("gwas_tool", "GWASAssociationByID")
    GWASStudyByID = _LazyImportProxy("gwas_tool", "GWASStudyByID")
    GWASSNPByID = _LazyImportProxy("gwas_tool", "GWASSNPByID")
    GWASVariantsForTrait = _LazyImportProxy("gwas_tool", "GWASVariantsForTrait")
    GWASAssociationsForTrait = _LazyImportProxy("gwas_tool", "GWASAssociationsForTrait")
    GWASAssociationsForSNP = _LazyImportProxy("gwas_tool", "GWASAssociationsForSNP")
    GWASStudiesForTrait = _LazyImportProxy("gwas_tool", "GWASStudiesForTrait")
    GWASSNPsForGene = _LazyImportProxy("gwas_tool", "GWASSNPsForGene")
    GWASAssociationsForStudy = _LazyImportProxy("gwas_tool", "GWASAssociationsForStudy")
    MCPClientTool = _LazyImportProxy("mcp_client_tool", "MCPClientTool")
    MCPAutoLoaderTool = _LazyImportProxy("mcp_client_tool", "MCPAutoLoaderTool")
    ADMETAITool = _LazyImportProxy("admetai_tool", "ADMETAITool")
    AlphaFoldRESTTool = _LazyImportProxy("alphafold_tool", "AlphaFoldRESTTool")
    ODPHPItemList = _LazyImportProxy("odphp_tool", "ODPHPItemList")
    ODPHPMyHealthfinder = _LazyImportProxy("odphp_tool", "ODHPHPMyHealthfinder")
    ODPHPTopicSearch = _LazyImportProxy("odphp_tool", "ODPHPTopicSearch")
    ODPHPOutlinkFetch = _LazyImportProxy("odphp_tool", "ODPHPOutlinkFetch")
    CellosaurusSearchTool = _LazyImportProxy(
        "cellosaurus_tool", "CellosaurusSearchTool"
    )
    CellosaurusQueryConverterTool = _LazyImportProxy(
        "cellosaurus_tool", "CellosaurusQueryConverterTool"
    )
    CellosaurusGetCellLineInfoTool = _LazyImportProxy(
        "cellosaurus_tool", "CellosaurusGetCellLineInfoTool"
    )
    # Literature search tools
    ArXivTool = _LazyImportProxy("arxiv_tool", "ArXivTool")
    CrossrefTool = _LazyImportProxy("crossref_tool", "CrossrefTool")
    DBLPTool = _LazyImportProxy("dblp_tool", "DBLPTool")
    PubMedTool = _LazyImportProxy("pubmed_tool", "PubMedTool")
    DOAJTool = _LazyImportProxy("doaj_tool", "DOAJTool")
    UnpaywallTool = _LazyImportProxy("unpaywall_tool", "UnpaywallTool")
    BioRxivTool = _LazyImportProxy("biorxiv_tool", "BioRxivTool")
    MedRxivTool = _LazyImportProxy("medrxiv_tool", "MedRxivTool")
    HALTool = _LazyImportProxy("hal_tool", "HALTool")
    CoreTool = _LazyImportProxy("core_tool", "CoreTool")
    PMCTool = _LazyImportProxy("pmc_tool", "PMCTool")
    ZenodoTool = _LazyImportProxy("zenodo_tool", "ZenodoTool")
    TextEmbeddingTool = _LazyImportProxy("text_embedding_tool", "TextEmbeddingTool")

__all__ = [
    "__version__",
    "ToolUniverse",
    "BaseTool",
    "register_tool",
    "get_tool_registry",
    "tools",
    "MonarchTool",
    "MonarchDiseasesForMultiplePhenoTool",
    "ClinicalTrialsSearchTool",
    "ClinicalTrialsDetailsTool",
    "OpentargetTool",
    "OpentargetGeneticsTool",
    "OpentargetToolDrugNameMatch",
    "DiseaseTargetScoreTool",
    "FDADrugLabelTool",
    "FDADrugLabelSearchTool",
    "FDADrugLabelSearchIDTool",
    "FDADrugLabelGetDrugGenericNameTool",
    "FDADrugAdverseEventTool",
    "FDACountAdditiveReactionsTool",
    "ChEMBLTool",
    "ComposeTool",
    "EuropePMCTool",
    "SemanticScholarTool",
    "PubTatorTool",
    "EFOTool",
    "AgenticTool",
    "DatasetTool",
    "SearchSPLTool",
    "GetSPLBySetIDTool",
    "HPAGetGeneJSONTool",
    "HPAGetGeneXMLTool",
    "ReactomeRESTTool",
    "PubChemRESTTool",
    "MedlinePlusRESTTool",
    "UniProtRESTTool",
    "PackageTool",
    "SMCP",
    "create_smcp_server",
    "USPTOOpenDataPortalTool",
    "XMLDatasetTool",
    "ToolFinderKeyword",
    "ToolFinderLLM",
    "URLHTMLTagTool",
    "URLToPDFTextTool",
    "RCSBTool",
    "GWASAssociationSearch",
    "GWASStudySearch",
    "GWASSNPSearch",
    "GWASAssociationByID",
    "GWASStudyByID",
    "GWASSNPByID",
    "GWASVariantsForTrait",
    "GWASAssociationsForTrait",
    "GWASAssociationsForSNP",
    "GWASStudiesForTrait",
    "GWASSNPsForGene",
    "GWASAssociationsForStudy",
    "MCPClientTool",
    "MCPAutoLoaderTool",
    "ADMETAITool",
    "default_tool_files",
    "EmbeddingDatabase",
    "EmbeddingSync",
    "ToolFinderEmbedding",
    "AlphaFoldRESTTool",
    "ODPHPMyHealthfinder",
    "ODPHPItemList",
    "ODPHPTopicSearch",
    "ODPHPOutlinkFetch",
    "CellosaurusSearchTool",
    "CellosaurusQueryConverterTool",
    "CellosaurusGetCellLineInfoTool",
    # Literature search tools
    "ArXivTool",
    "CrossrefTool",
    "DBLPTool",
    "PubMedTool",
    "DOAJTool",
    "UnpaywallTool",
    "BioRxivTool",
    "MedRxivTool",
    "HALTool",
    "CoreTool",
    "PMCTool",
    "ZenodoTool",
    "TextEmbeddingTool",
]
