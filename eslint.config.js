import eslintJs from '@eslint/js'
import eslintConfigPrettier from 'eslint-config-prettier'
import airbnb from 'eslint-config-airbnb-typescript'
import pluginImport from 'eslint-plugin-import'
import pluginReact from 'eslint-plugin-react'
import pluginReactHooks from 'eslint-plugin-react-hooks'
import reactConfigRecommended from 'eslint-plugin-react/configs/recommended.js'
import globals from 'globals'
import tseslint from 'typescript-eslint'
// import pluginUnusedImport from 'eslint-plugin-unused-imports'
import stylistic from '@stylistic/eslint-plugin'
// import stylisticJs from '@stylistic/eslint-plugin-js'
// import stylisticTs from '@stylistic/eslint-plugin-ts'
// import stylisticJsx from '@stylistic/eslint-plugin-jsx'

export default [
  stylistic.configs['recommended-flat'],
  stylistic.configs.customize({
    indent: 2,
    quotes: 'single',
    semi: false,
    jsx: true,
  }),
  eslintConfigPrettier,
  eslintJs.configs.recommended,
  // tseslint.configs.recommended,
  // eslintJs.configs.recommended,
  {
    ignores: ['./dist', 'eslint.config.js'],
  },
  {
    files: ['**/*.ts', '**/*.tsx'],

    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        project: true,
      },
    },

    plugins: {
      '@typescript-eslint': tseslint.plugin,
    },
    rules: {
      ...airbnb.rules,
      ...tseslint.plugin.configs['eslint-recommended'].rules,
      ...tseslint.plugin.configs.recommended.rules,
      // ...pluginTypeScript.configs['eslint-recommended'].rules,
      // ...pluginTypeScript.configs.recommended.rules,
      '@typescript-eslint/ban-types': 'error',
      // '@typescript-eslint/no-extra-semi': 'error',
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/explicit-function-return-type': 'error',
      '@typescript-eslint/no-unnecessary-type-assertion': 'error',
      '@typescript-eslint/no-unsafe-argument': 'error',
      '@typescript-eslint/no-unsafe-assignment': 'error',
      '@typescript-eslint/no-unsafe-call': 'error',
      '@typescript-eslint/no-unsafe-member-access': 'error',
      '@typescript-eslint/no-unsafe-return': 'error',
      '@typescript-eslint/require-await': 'error',
      '@typescript-eslint/typedef': 'error',
      '@typescript-eslint/no-unused-vars': ['error'],
    },
  },

  {
    files: ['**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx'],
    languageOptions: {
      globals: {
        ...globals.browser,
      },
      sourceType: 'module',
      parserOptions: {
        // project: ['./tsconfig.json', './tsconfig.node.json'],
        project: true,
      },
    },

    plugins: {
      react: pluginReact,
      '@react-hooks': pluginReactHooks,
      // '@stylisticJs': stylisticJs,
      '@stylistic': stylistic,
      import: pluginImport,
      // 'unused-imports': pluginUnusedImport,
    },

    rules: {
      // ...pluginImport.configs['recommended'].rules,
      ...reactConfigRecommended.rules,
      'react/jsx-uses-react': 'off',
      'react/react-in-jsx-scope': 'off',
      // ...stylistic.rules,
      // '@react-hooks/rules-of-hooks': 'error',
      // '@react-hooks/exhaustive-deps': 'warn',
      'no-unused-vars': 'off',
      'no-eq-null': 'off',
      'id-length': 'off',
      eqeqeq: 'off',
      // 'unused-imports/no-unused-imports': 'error',
      // '@stylistic/indent': ['error', 2],
      // '@stylistic/no-extra-semi': 'error',
      '@stylistic/semi-spacing': ['error', { after: true, before: false }],
      // '@stylistic/semi-style': ['error', 'last'],
      'no-console': 'off',
      'func-style': 'off',
      // 'import/no-extraneous-dependencies': ['error', { devDependencies: true }],
      '@stylistic/semi': ['error', 'never', { beforeStatementContinuationChars: 'never' }],
      '@stylistic/operator-linebreak': ['error', 'after'],
      '@stylistic/brace-style': ['error', '1tbs'],
      '@stylistic/jsx-quotes': ['error', 'prefer-single'],
      'no-undef': 'off',
      '@stylistic/multiline-ternary': 'off',
      '@stylistic/arrow-parens': 'off',
      // 'no-extra-semi': 'error',
      // 'no-unexpected-multiline': 'error',
      // 'no-unreachable': 'error',
      // 'import/prefer-default-export': 'off',
      'import/order': [
        'error',
        {
          groups: ['builtin', 'external', 'parent', 'sibling', 'index', 'object', 'type'],
          pathGroups: [
            {
              pattern: '{react,react-dom/**,react-router-dom}',
              group: 'builtin',
              position: 'before',
            },
          ],
          pathGroupsExcludedImportTypes: ['builtin'],
          alphabetize: {
            order: 'asc',
          },
          'newlines-between': 'never',
        },
      ],
      '@stylistic/member-delimiter-style': [
        'error',
        {
          multiline: {
            delimiter: 'none',
            requireLast: false,
          },
          singleline: {
            delimiter: 'semi',
            requireLast: false,
          },
        },
      ],
    },
  },
]
