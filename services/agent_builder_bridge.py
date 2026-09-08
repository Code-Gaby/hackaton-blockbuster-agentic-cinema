"""
services/agent_builder_bridge.py
================================
Google Cloud Agent Builder and Vertex AI Search Integration Bridge.

This module provides:
1. Google Cloud Agent Builder Tool and OpenAPI 3.0 specifications for Studio Co-Director.
2. Grounding bridge to Vertex AI Search and Conversation datastores when GCP is configured.
3. Exportable Agent Builder Manifest for direct import into Google Cloud Console.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("AgentBuilderBridge")

class GoogleCloudAgentBuilderBridge:
    """
    Integrates Agentic Cinema with Google Cloud Agent Builder (Vertex AI Search and Conversation).
    Provides enterprise grounding, tool definitions, and live datastore queries when configured.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        datastore_id: Optional[str] = None
    ):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.datastore_id = datastore_id or os.getenv("AGENT_BUILDER_DATASTORE_ID", "")
        self.is_connected = bool(self.project_id and self.datastore_id)
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initializes Vertex AI DiscoveryEngine / Agent Builder client if credentials exist."""
        if not self.is_connected:
            return
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine
            self.client = discoveryengine.SearchServiceClient()
            logger.info("Connected to Google Cloud Agent Builder (Vertex AI Search).")
        except Exception as e:
            logger.info(f"Agent Builder GCP client initialized in declarative spec mode: {e}")
            self.client = None

    def query_datastore(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Queries Google Cloud Agent Builder datastore for archival screenplay or studio documents."""
        if not self.client or not self.is_connected:
            return []
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine
            serving_config = (
                f"projects/{self.project_id}/locations/{self.location}"
                f"/dataStores/{self.datastore_id}/servingConfigs/default_serving_config"
            )
            req = discoveryengine.SearchRequest(
                serving_config=serving_config,
                query=query,
                page_size=max_results,
            )
            resp = self.client.search(req)
            results = []
            for r in resp.results:
                data = getattr(r, "document", None)
                if data:
                    results.append({
                        "id": getattr(data, "id", ""),
                        "title": getattr(data, "name", ""),
                        "snippet": str(getattr(data, "derived_struct_data", {}))
                    })
            return results
        except Exception as err:
            logger.warning(f"Error querying Agent Builder datastore: {err}")
            return []

    def get_agent_builder_spec(self, base_url: str = "https://agentic-cinema-studio.a.run.app") -> Dict[str, Any]:
        """
        Returns OpenAPI 3.0 Tool Specification formatted for Google Cloud Agent Builder.
        Can be registered directly as an Agent Extension / OpenAPI Tool in Vertex AI Agent Builder.
        """
        return {
            "openapi": "3.0.3",
            "info": {
                "title": "Agentic Cinema Studio — Agent Builder Co-Director Tools",
                "version": "1.0.0",
                "description": "Google Cloud Agent Builder tools for cinematic co-direction, narrative orchestration, and live location scouting via Parallel Search API."
            },
            "servers": [
                {"url": base_url, "description": "Production Cloud Run Studio API"}
            ],
            "paths": {
                "/api/scenes/{scene_id}/scout_parallel": {
                    "post": {
                        "summary": "Scout real-world filming locations using Parallel Search API",
                        "operationId": "scoutSceneWithParallel",
                        "parameters": [
                            {
                                "name": "scene_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "SQLite ID of the scene to scout locations for"
                            }
                        ],
                        "requestBody": {
                            "required": False,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "objective": {"type": "string", "description": "Specific search objective or criteria"},
                                            "lang": {"type": "string", "default": "EN"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Ranked real-world candidate locations with citations and diffs",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "success": {"type": "boolean"},
                                                "scene_id": {"type": "string"},
                                                "objective": {"type": "string"},
                                                "candidates": {"type": "array", "items": {"type": "object"}},
                                                "sources": {"type": "array", "items": {"type": "object"}}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/scenes/{scene_id}/apply_scouted_location": {
                    "post": {
                        "summary": "Apply approved scouted location into SQLite database (Zero Mutation Gate)",
                        "operationId": "applyScoutedLocation",
                        "parameters": [
                            {
                                "name": "scene_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["candidate_name", "location", "slugline"],
                                        "properties": {
                                            "candidate_name": {"type": "string"},
                                            "location": {"type": "string"},
                                            "slugline": {"type": "string"},
                                            "environmental_details": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Updated scene and production intelligence impact",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "success": {"type": "boolean"},
                                                "scene": {"type": "object"},
                                                "impact_message": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/chat": {
                    "post": {
                        "summary": "Director Agent conversational orchestration endpoint",
                        "operationId": "directorChat",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["message"],
                                        "properties": {
                                            "message": {"type": "string"},
                                            "project_id": {"type": "string"},
                                            "lang": {"type": "string", "default": "EN"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Director Agent response stream or JSON"
                            }
                        }
                    }
                }
            },
            "components": {
                "securitySchemes": {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-Studio-Api-Key"
                    }
                }
            }
        }

    def get_agent_builder_manifest(self) -> Dict[str, Any]:
        """Returns the Agent Builder Application Manifest describing the multi-agent system."""
        return {
            "name": "projects/" + (self.project_id or "agentic-cinema") + "/agents/studio-co-director",
            "displayName": "Agentic Cinema Studio — Studio Co-Director AI",
            "description": "Multi-agent autonomous film director powered by Gemini 2.5/3.5, Google Cloud Agent Builder, and Parallel Search API.",
            "defaultLanguageCode": "en",
            "supportedLanguageCodes": ["en", "es", "de", "fr", "it", "pt"],
            "timeZone": "UTC",
            "model": "gemini-2.5-flash",
            "tools": [
                {
                    "displayName": "ParallelSearchLocationScout",
                    "description": "Real-time web search tool via Parallel Search API to scout authentic film locations and historical facts.",
                    "openApiSpec": "#/paths/~1api~1scenes~1{scene_id}~1scout_parallel"
                },
                {
                    "displayName": "ZeroMutationGate",
                    "description": "Deterministic safety gate ensuring no film changes occur without explicit Director approval.",
                    "openApiSpec": "#/paths/~1api~1scenes~1{scene_id}~1apply_scouted_location"
                }
            ],
            "dataStores": [
                {
                    "displayName": "StudioCinemaProductionArchive",
                    "dataStoreId": self.datastore_id or "cinema-production-knowledge"
                }
            ] if self.datastore_id else []
        }

agent_builder_bridge = GoogleCloudAgentBuilderBridge()
