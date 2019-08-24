#!/usr/bin/env python3
#
#  Basic idea is to take the following input data
#     as detailed in ISC Bind v9 configuration file
#     for Access Control List (ACL) clause (configuration statement line).
#
#      acl transfer_bastion { };
#      acl hidden_masters { 192.168.1.52; 92.168.1.51; };
#      acl block_local { ! localhost; };
#      acl only_local { localhost; ! any; };
#      acl block_ten_and_eleven { ! { 10.0.0.0/8; 11.0.0.0/8; }; ! any; };
#
#  Note:  First set of curly braces demarks the set of Address
#             Match List (AML) element items (aka 'addr')
#  Note:  Exclamation can only be inside the first set of curly braces
#  Note:  Exclamation can only be before an element item (aka 'addr')
#  Note:  Subsequent nesting of curly brace set may have '!' inside or outside
#  Note:  Semicolon is used to terminate after each 'addr' or right curly braces.
#
#  And produce a suitable Pythonized list/dict which respect ordering
#  of these elements and its statements which is partially given below:
#
#  result = { 'acls':    # indexing each 'acl' statement (aka ISC Bind clause)
#               [        # '[' is a list, ordered-only, also multiple ACL statements
#                   {    # each '{' is an ACL statement

#                       'acl_name': 'transfer_bastion',   # first ACL statement
#                       'acl_addrs_list': []:
#                   },
#                   {
#                       'acl_name': 'block_ten_and_eleven',
#                       'acl_addrs_list':
#                       [
#                         # 'acl_addrs_brackets':
#                           {
#                               'not': '!',                    # exclamation/not is a dict-item
#                               'address_match_list':
#                               [                               # list('[') ordering matters here
#                                   {'addr': '10.0.0.0/8'},
#                                   {'addr': '11.0.0.0/8'},
#                               ]
#                           },
#                         # 'acl_addrs_w_not':
#                           {
#                                 'not': '!',                    # exclamation/not is a dict-item
#                                 {'addr': 'any'},
#                           }
#                         ]
#                   }
#               ]}
#           ]}
#
from pprint import PrettyPrinter
from pyparsing import Word, alphanums, Forward, ZeroOrMore, \
    Group, Literal, __diag__, Suppress, Char, \
    ParseSyntaxException, ParseBaseException, \
    ParseException, OneOrMore, Optional, Empty, \
    ungroup

progress = False
debug_flag = True

__diag__.enable("enable_debug_on_named_expressions")
__diag__.enable("warn_multiple_tokens_in_named_alternation")
__diag__.enable("warn_ungrouped_named_tokens_in_collection")
__diag__.enable("warn_name_set_on_empty_Forward")
__diag__.enable("warn_on_multiple_string_args_to_oneof")

pos = -1


def assertParseElement(a_parse_element, a_test_data, a_expected_result,
                       a_assert_flag=True):
    """
    A nice unit test tool which provides an assert()-like function
    that takes an string, parse the string, takes its computed
    Pythonized list/dict and compares the result against its
    expected Pythonized result.

    :param a_parse_element:  ParserElement class to exercise
    :param a_test_data:  A string in which to be parsed by a_parse_element
    :param a_expected_result:  A Python list in which to expect
    :param a_assert_flag:  If True, then expected result must match or an
                           exception gets raised.
                           If False, then parse MUST fail or expected
                           result does not match, else an exception
                           gets raised
    :return: Always returns True (exception handles the False, like
             an assert() class would do)
    """
    retsts = None

    try:
        a_parse_element = a_parse_element.setDebug(True)
        result = a_parse_element.parseString(a_test_data, parseAll=True)
        pp = PrettyPrinter(indent=2, width=66, compact=False)
        if result.asDict() == {}:
            print('***BAD***-Python-Dict result:', end='')
            pp.pprint(result)
        else:
            print('Good-Python-Dict result:')
            pp.pprint(result.asDict())
        print('expecting: ')
        pp.pprint(a_expected_result)
        # Convert ParserElement into Python List[] and compare
        retsts = (result.asDict() == a_expected_result)
    except ParseException as pe:
        print('ParseException:')
        print(pe.line)  # affected data content
        print(' ' * (pe.column - 1) + '^')  # Show where the error occurred
        print(pe)
        ParseException.explain(pe)
        retsts = False
    except ParseBaseException as pe:
        print('ParseBaseException:')
        print(a_test_data)  # affected data content
        print(' ' * (pe.column - 1) + '^')  # Show where the error occurred
        print(pe)
        retsts = False
    except ParseSyntaxException as pe:
        print('ParseSyntaxException:')
        print(a_test_data)  # affected data content
        print(' ' * (pe.column - 1) + '^')  # Show where the error occurred
        print(pe)
        retsts = False
    if retsts == a_assert_flag:
        print('assert(True)')
        return True
    else:
        print('assert(***FALSE***)')
        errmsg = 'Error(assert=' + str(False) + '): \"' + a_test_data + '\".'
        raise SyntaxError(errmsg)


def assertParseElementTrue(at_parse_element, at_test_data, at_expected_result):
    """
    A nice wrapper routine to ensure that the word 'True' is in the
    function name.
    """
    assertParseElement(a_parse_element=at_parse_element,
                       a_test_data=at_test_data,
                       a_expected_result=at_expected_result,
                       a_assert_flag=True)


def assertParseElementFalse(af_parse_element, af_test_data, af_expected_result):
    """
    A nice wrapper routine to ensure that the word 'False' is in the
    function name.
    """
    assertParseElement(a_parse_element=af_parse_element,
                       a_test_data=af_test_data,
                       a_expected_result=af_expected_result,
                       a_assert_flag=False)


addr = Word(alphanums + '_-./:').setResultsName('addr').setName('<addr>')
semicolon, lbrack, rbrack = map(Suppress, ';{}')
exclamation = Char('!')

addr_choices_series = Group(
    ZeroOrMore(
        Group(
            Optional(exclamation)('not')
            + addr
            + semicolon
        )
    )
)('addr_series')

aml_nesting = Forward()
aml_nesting << (
    (
            (
                    Optional(exclamation('not'))
                    - lbrack
                    - aml_nesting
                    - rbrack
                    - semicolon
            )
            | (
                #            Group(
                ZeroOrMore(
                    #                    Group(
                    Optional(exclamation)('not')
                    + addr_choices_series
                    + semicolon
                    #                    )
                )
                #            )
                # | addr_choices_series
            )
    )
)('aml_nesting')  # ('addr_choices_forward*')

addr_first_nest_list = (
    (
        # first nesting has no exclamation outside of its curly braces.
            lbrack
            - (
                (
                    Group(
                        addr_choices_series
#                        aml_nesting
                    )
                )
            )
            + rbrack
            + semicolon
    )
)('aml_series')

clause_stmt_acl_standalone = (
    (
            Literal('acl').suppress()
            + Word(alphanums + '_-')('acl_name')
            + addr_first_nest_list
    )
)

# Syntax:
#         acl a { b; };  acl c { d; e; f; }; acl g { ! h; ! { i; }; };
#
clause_stmt_acl_series = ZeroOrMore(
    Group(
        clause_stmt_acl_standalone
    )
)('acls')

#######################################################
#  Unit tests of ACL statements
#######################################################
# Null tests
assertParseElementTrue(aml_nesting, ' ', {'aml_nesting': []})  # something to aml_nesting
assertParseElementTrue(addr_choices_series, ' ', {'addr_series': []})  # False; always supply something to aml_nesting
assertParseElementFalse(clause_stmt_acl_standalone, ' ', {})  # this always expects an ACL statement
assertParseElementTrue(clause_stmt_acl_series, ' ', {})  # check for null

# A simple ACL element
assertParseElementTrue(
    addr_choices_series,
    'only_element;',
    {
        'addr_series': [
            {'addr': 'only_element'},
            ]})
# A simple not ACL element
assertParseElementTrue(
    addr_choices_series,
    '! only_element;',
    {
        'addr_series': [
            {'addr': 'only_element', 'not': '!'},
            ]})
# A simple series of three ACL elements
assertParseElementTrue(
    addr_choices_series,
    'element1; element2; element3;',
    {
        'addr_series': [
            {'addr': 'element1'},
            {'addr': 'element2'},
            {'addr': 'element3'},
            ]})

# A simple series of three 'knotted' ACL elements
assertParseElementTrue(
    addr_choices_series,
    '! not_element1; ! knot_element2; ! nyot_element3;',
    {
        'addr_series': [
            {'addr': 'not_element1', 'not': '!'},
            {'addr': 'knot_element2', 'not': '!'},
            {'addr': 'nyot_element3', 'not': '!'},
            ]})

# First nesting of a simple element
assertParseElementTrue(
    addr_first_nest_list,
    '{ cat_1; };',
    {
        'aml_series': [
            {
                'addr_series': [
                    {'addr': 'cat_1'},
                    ]}
        ]})

# First nesting of a simple element
assertParseElementTrue(
    addr_first_nest_list,
    '{ via_1; via_2; via_3; };',
    {
        'aml_series': [{
                'addr_series': [
                    {'addr': 'via_1'},
                    {'addr': 'via_2'},
                    {'addr': 'via_3'},
                    ]}
        ]})

# First nesting of a simple element
assertParseElementTrue(
    addr_first_nest_list,
    '{ boa_1; ! boa_2; boa_3; };',
    {
        'aml_series': [
            {
                'addr_series': [
                    {'addr': 'boa_1'},
                    {'addr': 'boa_2', 'not': '!'},
                    {'addr': 'boa_3'},
                    ]}
        ]}
)

# Simplest ACL statement
test_data = 'acl simplest { statement; };'
expected_result = {
    'acl_name': 'simplest',
    'aml_series': [
        {
            'addr_series': [
                {'addr': 'statement'}
                ]}
        ]}

assertParseElementTrue(clause_stmt_acl_standalone, test_data, expected_result)
expected_result = {'acls': [expected_result]}  # add the series and retest
assertParseElementTrue(clause_stmt_acl_series, test_data, expected_result)

if progress:
    assertParseElementTrue(
        clause_stmt_acl_standalone,
        'acl null { };',
        {'acl_name': 'null', 'aml_series': []}
    )
# A simple statement using an exclamation ('!')
assertParseElementTrue(
    clause_stmt_acl_series.setDebug(True),
    'acl simplest_statement { ! simple_statement_w_exclamation; };',
    {
        'acls': [
            {
                'acl_name': 'simplest_statement',
                'aml_series': [
                    {
                        'addr_series': [
                            {'addr': 'simple_statement_w_exclamation', 'not': '!'}
                            ]}
                    ]}
            ]}
)

# A simple series of address elements
assertParseElementTrue(
    clause_stmt_acl_standalone,
    'acl single_statement { series; of; elements; };',
    {
        'acl_name': 'single_statement',
        'aml_series': [
            {
                'addr_series': [
                    {'addr': 'series'},
                    {'addr': 'of'},
                    {'addr': 'elements'},
                    ]}
            ]}
)

# A simple series of three ACL statements
assertParseElementTrue(
    clause_stmt_acl_series,
    'acl first_statement { element1; }; acl second { element2; }; acl third { element3; };',
    {
        'acls': [
            {
                'acl_name': 'first_statement',
                'aml_series': [
                    {
                        'addr_series': [
                            {'addr': 'element1'}
                            ]}
                ]},
            {
                'acl_name': 'second',
                'aml_series': [
                    {
                        'addr_series': [
                            {'addr': 'element2'}
                            ]}
                ]},
            {
                'acl_name': 'third',
                'aml_series': [
                    {
                        'addr_series': [
                            {'addr': 'element3'}
                        ]}
                ]}
        ]}
)

assertParseElementTrue(
    clause_stmt_acl_series,
    'acl new_series { master_nameservers; slave_nameservers; };',
    {
        'acls': [
            {
                'acl_name': 'new_series',
                'aml_series': [
                    {
                        'addr_series': [
                            {'addr': 'master_nameservers'},
                            {'addr': 'slave_nameservers'}
                        ]}
                ]}
        ]}
)

assertParseElementTrue(
    clause_stmt_acl_series,
    'acl my_acl_name { master_nameservers; slave_nameservers; }; acl a { b; };',
    {
        'acls': [
            {
                'acl_name': 'my_acl_name',
                'aml_series': [
                    {
                        'addr_series': [
                            {'addr': 'master_nameservers'},
                            {'addr': 'slave_nameservers'},
                        ]},
                ]},
            {
                'acl_name': 'a',
                'aml_series': [
                    {
                        'addr_series': [
                            {'addr': 'b'}
                        ]}
                ]}
        ]}
)
test_data = 'acl target_acl { master_nameservers; ! slave_nameservers; }; acl a { ! b; };'
expected_result = {
    'acls': [
        {
            'acl_name': 'target_acl',
            'aml_series': [
                {
                    'addr_series': [
                        {'addr': 'master_nameservers'},
                        {'addr': 'slave_nameservers', 'not': '!'}
                    ]}
             ]},
        {
            'acl_name': 'a',
            'aml_series': [
                {
                    'addr_series': [
                        {'addr': 'b', 'not': '!'}
                    ]}
            ]}
    ]}
assertParseElementTrue(clause_stmt_acl_series, test_data, expected_result)

######################################################3
#  Standalone ACL statement
#######################################################

assertParseElementTrue(
    clause_stmt_acl_standalone,
    'acl transfer_bastions { };',
    {
        'acl_name': 'transfer_bastions',
        'aml_series': [
            {'addr_series': []}
        ]}
)
assertParseElementTrue(
    clause_stmt_acl_standalone,
    'acl one { 1.1.1.1; };',
    {
        'acl_name': 'one',
        'aml_series': [
            {
                'addr_series': [
                    {'addr': '1.1.1.1'}
                ]}
        ]}
)
assertParseElementTrue(
    clause_stmt_acl_standalone,
    'acl one { ! 23.23.23.23; };',
    {
        'acl_name': 'one',
        'aml_series': [
            {
                'addr_series': [
                    {'addr': '23.23.23.23', 'not': '!'}
                ]}
        ]}
)
assertParseElementTrue(
    clause_stmt_acl_standalone,
    'acl one { ! 24.24.24.24; };',
    {
        'acl_name': 'one',
        'aml_series': [  # '[' supports series of 'aml'
            {  # '{' supports each elements';' within each 'aml'
                'addr_series': [
                    {
                        'addr': '24.24.24.24',
                        'not': '!'
                    }
                ]}
        ]}
)
assertParseElementTrue(
    clause_stmt_acl_standalone,
    'acl one { ! 8.8.8.8; };',
    {
        'acl_name': 'one',
        'aml_series': [
            {
                'addr_series': [
                    {'addr': '8.8.8.8', 'not': '!'}
                ]}
        ]}
)
assertParseElementTrue(
    clause_stmt_acl_standalone,
    'acl aaa { bbb; };',
    {
        'acl_name': 'aaa',
        'aml_series': [
            {
                'addr_series': [
                    {'addr': 'bbb'}
                ]}
        ]}
)

test_data = 'acl my_element_is_not { ! knotted_element; };'
expected_result = {
    'acl_name': 'my_element_is_not',
    'aml_series': [
        {
            'addr_series': [
                {
                    'addr': 'knotted_element',
                    'not': '!'
                }
            ]}
    ]}
assertParseElementTrue(clause_stmt_acl_standalone, test_data, expected_result)
expected_result = {'acls': [expected_result]}  # add the series and retest
assertParseElementTrue(clause_stmt_acl_series, test_data, expected_result)

# Bug #1?: Pretty sure that aml_nesting ParserElement should have
#          provided the Optional(exclamation) here:
#
# Match {Suppress:("acl") W:(ABCD...) {Suppress:("{") - Group:(Group:([Group:({[W:(!)] <addr> Suppress:(";")})]...)) Suppress:("}") Suppress:(";")}} at loc 0(1,1)
# Match {Suppress:("{") - Group:(Group:([Group:({[W:(!)] <addr> Suppress:(";")})]...)) Suppress:("}") Suppress:(";")} at loc 14(1,15)
# Match Group:([Group:({[W:(!)] <addr> Suppress:(";")})]...) at loc 17(1,18)
# Match <addr> at loc 18(1,19)
# Exception raised:Expected <addr>, found '{'  (at char 19), (line:1, col:20)
# Matched Group:([Group:({[W:(!)] <addr> Suppress:(";")})]...) -> [[]]
# Exception raised:Expected "}", found '!'  (at char 17), (line:1, col:18)
# Exception raised:Expected "}", found '!'  (at char 17), (line:1, col:18)
# ParseBaseException:
# acl nested_aml { ! { name_5015; name_5016; }; };
#                  ^
# Expected "}", found '!'  (at char 17), (line:1, col:18)
# assert(***FALSE***)
assertParseElementTrue(
    clause_stmt_acl_standalone,
    'acl nested_aml { ! { name_5015; name_5016; }; };',
    {
        'acl_name': 'nested_aml',
        'aml_series': [  # first set of curly braces
            {
                'addr_series': [  # second set of curly braces
                    {'acl_name': 'name_5015', 'not': ''},
                    {'acl_name': 'name_5016', 'not': ''}
                ]}
        ]}
)


# BUG #2?   Nestings got consolidated into a single nest
#
#  Computed result on Python 3.7 is:
#
# Match {Suppress:("acl") W:(ABCD...) {Suppress:("{") - Group:(Group:([Group:({[W:(!)] <addr> Suppress:(";")})]...)) Suppress:("}") Suppress:(";")}} at loc 0(1,1)
# Match {Suppress:("{") - Group:(Group:([Group:({[W:(!)] <addr> Suppress:(";")})]...)) Suppress:("}") Suppress:(";")} at loc 19(1,20)
# Match Group:([Group:({[W:(!)] <addr> Suppress:(";")})]...) at loc 22(1,23)
# Match <addr> at loc 23(1,24)
# Exception raised:Expected <addr>, found '{'  (at char 24), (line:1, col:25)
# Matched Group:([Group:({[W:(!)] <addr> Suppress:(";")})]...) -> [[]]
# Exception raised:Expected "}", found '!'  (at char 22), (line:1, col:23)
# Exception raised:Expected "}", found '!'  (at char 22), (line:1, col:23)
# ParseBaseException:
# acl nested_aml_nots { ! { ! { ! master_nameservers; }; }; };
#                       ^
# Expected "}", found '!'  (at char 22), (line:1, col:23)
# assert(***FALSE***)
#
#
test_data = 'acl nested_aml_nots { ! { ! { ! master_nameservers; }; }; };'
expected_result = {
    'acl_name': 'nested_aml_nots',
    'aml_series': [
        {
            'addr_series':
                {
                    'addr_series':
                        {
                            'acl_name': 'master_nameservers',
                            'not': '!'
                        },
                    'not': '!'
                },
            'not': '!'
        },
    ],
}
assertParseElementTrue(clause_stmt_acl_standalone, test_data, expected_result)
expected_result = {'acls': [expected_result]}  # add the series and retest
assertParseElementTrue(clause_stmt_acl_series, test_data, expected_result)

assertParseElementTrue(
    clause_stmt_acl_standalone,
    'acl a_set { sfirst_set; { second_set; sa_third_set; }; };',
    {
        'acl_name': ' a_set',
        'aml_series':
            [
                {'acl_name': 'sfirst_set', 'not': ''},
                {
                    'aml':
                        [
                            {'acl_name': 'second_set', 'not': ''},
                            {'acl_name': 'sa_third_set', 'not': ''},
                        ]
                }
            ]
    }

)

exit(77)
