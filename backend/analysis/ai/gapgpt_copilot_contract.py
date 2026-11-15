CONTRACT = {
    'type': 'object', 'additionalProperties': False, 'required': ['conversation', 'answer_plan'],
    'properties': {
        'conversation': {
            'type': 'object', 'additionalProperties': False,
            'required': ['acknowledgement', 'next_question', 'brief_proposal'],
            'properties': {
                'acknowledgement': {'type': 'string', 'maxLength': 300},
                'next_question': {'type': ['string', 'null'], 'maxLength': 220},
                'brief_proposal': {
                    'type': 'object', 'maxProperties': 6,
                    'description': 'User-reported ShoppingBrief changes proposed for confirmation; never applied automatically.',
                },
            },
        },
        'answer_plan': {
            'type': 'object', 'additionalProperties': False,
            'required': ['answer_type', 'lead_key', 'clarification_key', 'blocks'],
            'properties': {
                'answer_type': {'type': 'string'}, 'lead_key': {'type': 'string'},
                'clarification_key': {'type': 'string'}, 'blocks': {'type': 'array', 'maxItems': 3},
            },
        },
    },
}
