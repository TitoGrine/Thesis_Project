profile_index_mapping = {
    "mappings": {
        "properties": {
            "id": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                    }
                }
            },
            "username": {
                "type": "text"
            },
            "name": {
                "type": "text"
            },
            "profile_image": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                    }
                }
            },
            "location": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                    }
                }
            },
            "description": {
                "type": "text"
            },
            "entities": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                    }
                }
            },
            "score": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                    }
                }
            },
            "processed_links": {
                "type": "nested",
                "properties": {
                    "description": {
                        "type": "text"
                    },
                    "emails": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                            }
                        }
                    },
                    "entities": {
                        "type": "nested",
                        "properties": {
                            "location": {
                                "type": "text",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword",
                                    }
                                }
                            },
                            "norp": {
                                "type": "text",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword",
                                    }
                                }
                            },
                            "organization": {
                                "type": "text",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword",
                                    }
                                }
                            },
                            "person": {
                                "type": "text",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword",
                                    }
                                }
                            }
                        }
                    },
                    "external_links": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                            }
                        }
                    },
                    "images": {
                        "type": "nested",
                        "properties": {
                            "alt": {
                                "type": "text",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword",
                                    }
                                }
                            },
                            "width": {
                                "type": "long"
                            },
                            "height": {
                                "type": "long"
                            },
                            "src": {
                                "type": "text",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword",
                                    }
                                }
                            },
                            "type": {
                                "type": "text",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword",
                                    }
                                }
                            }
                        }
                    },
                    "internal_links": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                            }
                        }
                    },
                    "is_link_tree": {
                        "type": "boolean"
                    },
                    "keywords": {
                        "type": "text"
                    },
                    "name": {
                        "type": "text"
                    },
                    "original_link": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                            }
                        }
                    },
                    "score": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                            }
                        }
                    },
                    "title": {
                        "type": "text"
                    }
                }
            },
            "unprocessed_links": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                    }
                }
            },
        }
    }
}
