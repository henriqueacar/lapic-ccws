const Errors = [
    {
        "error": 101,
        "description": "Illegal argument [argumentName] value"
    },
];

exports.getError = (number) => {
    return Errors.filter(errors => errors.error == number)[0];
}