export const name = 'lesson-count-codepoints'
export const inject = ['tools']

export function apply(ctx) {
  ctx.tools.register({
    name: 'count_codepoints',
    description: 'Count the Unicode code points in a string.',
    parameters: {
      type: 'object',
      properties: { text: { type: 'string' } },
      required: ['text'],
      additionalProperties: false,
    },
    async execute(args) {
      if (typeof args?.text !== 'string' || Object.keys(args).length !== 1) {
        throw new TypeError('Expected one string argument named text')
      }
      return Array.from(args.text).length
    },
    output: {
      schema: { type: 'integer' },
      render: (_args, count) => [{ type: 'text', text: String(count) }],
    },
  })
}
