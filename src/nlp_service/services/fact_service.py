from nlp_service.services import ml_service, response_strings
from nlp_service.services.response_strings import Responses
from postgresql_db.models import FactEntity, Fact, FactType


def get_resolved_fact_keys(conversation):
    """
    Returns a list of all the resolved facts for a conversation as string keys
    :param conversation: The current conversation
    :return: List of all resolved fact names as strings
    """
    return [fact_entity_row.fact.name for fact_entity_row in conversation.fact_entities]


def submit_claim_category(conversation):
    """
    Returns the first fact after submitting a determined claim category
    :param conversation: The current conversation
    :return: First fact id to ask a question for
    """

    return {
        'fact_id': get_next_fact(conversation)
    }


def submit_resolved_fact(conversation, current_fact, entity_value):
    """
    After resolving a fact, returns the next fact to ask a question for
    :param conversation: The current conversation
    :param current_fact: The current fact
    :param entity_value: Classified value of the current fact
    :return: Next fact id to ask a question for
    """

    # Create new FactEntity and attach to conversation
    fact_entity = FactEntity(fact=current_fact, value=entity_value)
    conversation.fact_entities.append(fact_entity)

    # Get all resolved facts for Conversation
    facts_resolved = get_resolved_fact_keys(conversation)

    return {
        'fact_id': get_next_fact(conversation)
    }


# Dictionary that maps claim categories to outcomes. Facts from these outcomes will be used to
# ask questions to users for a particular claim category
outcome_mapping = {
    "lease_termination": [
        "orders_resiliation"
    ],
    "nonpayment": [
        "tenant_ordered_to_pay_landlord",
        "tenant_ordered_to_pay_landlord_legal_fees",
        "additional_indemnity_money"
    ]
}


def replace_anti_facts(fact_list, anti_fact_dict):
    for fact in fact_list:
        if fact not in Responses.fact_questions.keys():
            fact_list.remove(fact)
            if fact in anti_fact_dict.keys():
                fact_list.append(anti_fact_dict[fact])
            elif fact in anti_fact_dict.values():
                fact_list.append([k for k, v in anti_fact_dict.items() if v == fact][0])

    return fact_list


def get_category_fact_list(claim_category):
    """
    Returns a dict containing a list fo important facts "facts", and non-important facts "additional_facts" for a claim category
    :param claim_category: Claim category as a string
    """
    category_fact_dict = {
        "facts": [],
        "additional_facts": []
    }
    all_category_outcomes = outcome_mapping[claim_category.value.lower()]

    outcome_facts = ml_service.get_outcome_facts()
    for outcome in outcome_facts:
        if outcome in all_category_outcomes:
            category_fact_dict["facts"].extend(outcome_facts[outcome]["important_facts"])
            category_fact_dict["additional_facts"].extend(outcome_facts[outcome]["additional_facts"])

    # Remove Duplicates
    category_fact_dict["facts"] = list(set(category_fact_dict["facts"]))
    category_fact_dict["additional_facts"] = list(set(category_fact_dict["additional_facts"]))

    # Replace anti facts with askable facts, if applicable
    category_fact_dict["facts"] = replace_anti_facts(category_fact_dict["facts"], ml_service.get_anti_facts())
    category_fact_dict["additional_facts"] = replace_anti_facts(category_fact_dict["additional_facts"],
                                                                ml_service.get_anti_facts())

    # Filter out unaskable facts
    category_fact_dict["facts"] = [fact for fact in category_fact_dict["facts"] if
                                   fact in Responses.fact_questions.keys()]
    category_fact_dict["additional_facts"] = [fact for fact in category_fact_dict["additional_facts"] if
                                              fact in Responses.fact_questions.keys()]

    return category_fact_dict


def get_next_fact(conversation):
    """
    Returns next fact id based on claim category given the resolved facts.
    :param conversation: The current conversation
    :return: Next fact id to ask a question for
    """

    all_category_facts = get_category_fact_list(conversation.claim_category.value)
    facts_resolved = get_resolved_fact_keys(conversation)
    facts_unresolved = []

    if has_important_facts(conversation):
        facts_unresolved = [fact for fact in all_category_facts["facts"] if fact not in facts_resolved]
    elif has_additional_facts(conversation):
        facts_unresolved = [fact for fact in all_category_facts["additional_facts"] if fact not in facts_resolved]

    fact_name = facts_unresolved[0]
    fact = Fact.query.filter_by(name=fact_name).first()
    return fact.id


def has_important_facts(conversation):
    """
    Returns true of important facts still exist for this conversation
    :param conversation: The current conversation
    :return:
    """
    all_category_facts = get_category_fact_list(conversation.claim_category.value)
    facts_resolved = get_resolved_fact_keys(conversation)
    facts_unresolved = [fact for fact in all_category_facts["facts"] if fact not in facts_resolved]
    if len(facts_unresolved) == 0:
        return False
    return True


def has_additional_facts(conversation):
    """
    Returns true of additional facts still exist for this conversation
    :param conversation: The current conversation
    :return:
    """
    all_category_facts = get_category_fact_list(conversation.claim_category.value)
    facts_resolved = get_resolved_fact_keys(conversation)
    facts_unresolved = [fact for fact in all_category_facts["additional_facts"] if fact not in facts_resolved]
    if len(facts_unresolved) == 0:
        return False
    return True


def extract_fact_by_type(fact_type, intent, entities):
    """
    Returns the relevant information for a particular FactType based on rasa nlu classification data.
    :param fact_type: The FactType of the relevant fact
    :param intent: The intent returned by RASA. Has 'name' and 'confidence' attributes.
    :param entities: A list of extracted entities. Can be empty.
    :return: Final fact value based on fact_type
    """

    intent_name = intent['name']

    if fact_type == FactType.BOOLEAN:
        return intent_name
    elif fact_type == FactType.MONEY:
        if intent_name == 'true':
            for entity in entities:
                if entity['entity'] == 'amount-of-money':
                    return entity['value']
        elif intent_name == 'false':
            return 0
