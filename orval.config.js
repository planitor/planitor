module.exports = {
  planitor: {
    output: {
      target: "src/api/types.ts",
      client: "react-query",
      override: {
        mutator: {
          path: "src/api/client.ts",
          name: "client",
        },
      },
    },
    input: { target: "./openapi.json", validate: false },
  },
};
