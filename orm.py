from bson.objectid import InvalidId, ObjectId

import collections
import datetime


class ValidationError(Exception):
    pass

# Fields

# Field decorators


# decorator that handles default serialization for all fields
def serialize_super(none_value=None):
    def serialize_outer(serialize):
        def serialize_wrapper(self, value, context, obj):
            if value is None:
                if callable(none_value):
                    return none_value()
                else:
                    return none_value
            return serialize(self, value, context, obj)
        return serialize_wrapper
    return serialize_outer


# decorator that handles default unserialization for all fields
def unserialize_super(none_value=None):
    def unserialize_outer(unserialize):
        def unserialize_wrapper(self, value, context, data):
            if value is None:
                if callable(none_value):
                    return none_value()
                else:
                    return none_value
            return unserialize(self, value, context, data)
        return unserialize_wrapper
    return unserialize_outer


# decorator that handles default validation for all fields
def validate_super(validate):
    def validate_wrapper(self, value):
        if not Field.validate(self, value):
            return False

        if value is None:
            return True

        return validate(self, value)
    return validate_wrapper


class Field(object):

    def __init__(self, default=None,
                 required=False,
                 validators=None,
                 load_from=None,
                 dump_to=None):
        self.default = default
        self.required = required
        self.validators = validators
        self.load_from = load_from
        self.dump_to = dump_to

    def serialize(self, value, context, obj):
        raise NotImplementedError

    def unserialize(self, value, context, data):
        raise NotImplementedError

    def validate(self, value):
        if self.required and (value is None):
            return False

        if self.validators:
            for validator in self.validators:
                if not validator(value):
                    return False

        return True


class BooleanField(Field):

    @serialize_super()
    def serialize(self, value, context, obj):
        return value

    @unserialize_super()
    def unserialize(self, value, context, data):
        if not isinstance(value, bool):
            return None
        else:
            return value

    @validate_super
    def validate(self, value):
        return isinstance(value, bool)


class DateTimeField(Field):

    @serialize_super()
    def serialize(self, value, context, obj):
        if context == 'db':
            return value
        elif context == 'web':
            return value.strftime("%x")

    @unserialize_super()
    def unserialize(self, value, context, data):
        if context == 'db':
            return value
        elif context == 'web':
            try:
                return datetime.datetime.strptime(value, "%x")
            except ValueError:
                # TODO: log this error
                return None

    @validate_super
    def validate(self, value):
        return isinstance(value, datetime.datetime)


class DictField(Field):

    def __init__(self, from_field, to_field, *args, **kwargs):
        self.from_field = from_field
        self.to_field = to_field
        super(DictField, self).__init__(*args, **kwargs)

    @serialize_super(none_value=dict)
    def serialize(self, value, context, obj):
        return {self.from_field.serialize(k, context, obj): self.to_field.serialize(v, context, obj)
                for k, v in value.items()}

    @unserialize_super(none_value=dict)
    def unserialize(self, value, context, data):
        if not isinstance(value, dict):
            return dict()
        return {self.from_field.unserialize(k, context, data): self.to_field.unserialize(v, context, data)
                for k, v in value.items()}

    @validate_super
    def validate(self, value):
        if not isinstance(value, dict):
            return False

        for k, v in value.items():
            if not self.from_field.validate(k):
                return False
            if not self.to_field.validate(v):
                return False
        return True


class DocumentField(Field):

    def __init__(self, document_type, *args, **kwargs):
        self.document_type = document_type
        super(DocumentField, self).__init__(self, *args, **kwargs)

    @serialize_super()
    def serialize(self, value, context, obj):
        return value.dump(context, validate_on_dump=False)

    @unserialize_super()
    def unserialize(self, value, context, data):
        try:
            return self.document_type().load(value, context, validate_on_load=False)
        except:
            return None

    @validate_super
    def validate(self, value):
        return isinstance(value, self.document_type)


class FloatField(Field):

    @serialize_super()
    def serialize(self, value, context, obj):
        return value

    @unserialize_super()
    def unserialize(self, value, context, data):
        if not isinstance(value, (float, int, long)):
            return None
        else:
            return float(value)

    @validate_super
    def validate(self, value):
        return isinstance(value, float)


class IntField(Field):

    @serialize_super()
    def serialize(self, value, context, obj):
        return value

    @unserialize_super()
    def unserialize(self, value, context, data):
        if not isinstance(value, int):
            return None
        else:
            return value

    @validate_super
    def validate(self, value):
        return isinstance(value, int)


class ListField(Field):

    def __init__(self, field_type, *args, **kwargs):
        self.field_type = field_type
        self.field_type.required = True  # don't allow Nones in list
        super(ListField, self).__init__(*args, **kwargs)

    @serialize_super(none_value=list)
    def serialize(self, value, context, obj):
        return [self.field_type.serialize(v, context, obj) for v in value]

    @unserialize_super(none_value=list)
    def unserialize(self, value, context, data):
        if not isinstance(value, collections.Iterable):
            return []
        return [self.field_type.unserialize(v, context, data) for v in value]

    @validate_super
    def validate(self, value):
        if not isinstance(value, list):
            return False

        for v in value:
            if not self.field_type.validate(v):
                return False

        return True


class ObjectIDField(Field):

    @serialize_super()
    def serialize(self, value, context, obj):
        if context == 'db':
            return value
        elif context == 'web':
            return str(value)

    @unserialize_super()
    def unserialize(self, value, context, data):
        if context == 'db':
            return value
        elif context == 'web':
            try:
                return ObjectId(value)
            except InvalidId:
                # TODO: log this error
                return None

    @validate_super
    def validate(self, value):
        return isinstance(value, ObjectId)


class StringField(Field):

    @serialize_super()
    def serialize(self, value, context, obj):
        if isinstance(value, unicode):
            # TODO: figure out a better Unicode strategy
            return value.encode('ascii', 'ignore')
        elif isinstance(value, str):
            return value
        else:
            return None

    @unserialize_super()
    def unserialize(self, value, context, data):
        if isinstance(value, unicode):
            return value.encode('ascii', 'ignore')
        elif isinstance(value, str):
            return value
        else:
            return None

    @validate_super
    def validate(self, value):
        return isinstance(value, (str, unicode))

# Field validators


def validate_choices(choices):
    return (lambda x: x in choices)

# Documents


class Document(object):
    fields = []

    def __init__(self, **kwargs):
        for field_name, field in self.fields:
            field_value = kwargs.get(field_name)
            if field_value is None:
                self.__setattr__(field_name, field.default)
            else:
                self.__setattr__(field_name, kwargs.get(field_name))

        self.post_init()

    def __repr__(self):
        field_strs = []
        for field_name, field in self.fields:
            field_value = self.__getattribute__(field_name)
            field_strs.append("{}: {}".format(field_name, field_value))
        return '{{{}}}'.format(', '.join(field_strs))

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        if other is None:
            return False
        return all([self.__getattribute__(field_name) == other.__getattribute__(field_name)
                    for field_name, _ in self.fields])

    def __ne__(self, other):
        return not self == other

    def dump(self, context=None, exclude=None, only=None, validate_on_dump=True):
        return_dict = {}

        if validate_on_dump and not self.validate():
            is_valid, errors = self.validate()
            if not is_valid:
                raise ValidationError(str(errors))

        for field_name, field in self.fields:
            if exclude is not None and field_name in exclude:
                continue
            if only is not None and field_name not in only:
                continue

            field_value = self.__getattribute__(field_name)

            to_name = field_name
            if field.dump_to is not None:
                if isinstance(field.dump_to, dict):
                    to_name = field.dump_to.get(context, field_name)
                elif isinstance(field.dump_to, str):
                    to_name = field.dump_to

            return_dict[to_name] = field.serialize(field_value, context, self)

        return return_dict

    @classmethod
    def load(cls, data, context=None, validate_on_load=True, strict=False):
        if not isinstance(data, dict):
            if strict:
                raise ValidationError("can only load data from dicts")
            return None

        init_args = dict()
        for field_name, field in cls.fields:
            from_name = field_name
            if field.load_from is not None:
                if isinstance(field.load_from, dict):
                    from_name = field.load_from.get(context, field_name)
                elif isinstance(field.load_from, str):
                    from_name = field.load_from

            field_value = field.unserialize(data.get(from_name), context, data)
            if field_value is None:
                init_args[field_name] = field.default
            else:
                init_args[field_name] = field_value

        return_document = cls(**init_args)

        if validate_on_load and not return_document.validate():
            if strict:
                raise ValidationError
            return None

        return return_document

    def validate(self):
        if not self.validate_document():
            return False, 'validate_document'

        for field_name, field in self.fields:
            field_value = self.__getattribute__(field_name)
            if not field.validate(field_value):
                return False, 'validate_field ({})'.format(field_name)

        return True, None

    # override to do something (i.e. initialize properties) post-init/load
    def post_init(self):
        pass

    # override for document-wide validation
    def validate_document(self):
        return True
